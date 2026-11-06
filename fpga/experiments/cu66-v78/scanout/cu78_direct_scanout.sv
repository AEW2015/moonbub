`timescale 1ns/1ps
// Continuous immutable-source scanout. Cache epochs repeat at native refresh;
// committed source identity changes only after old reads drain, at vblank.
module cu78_direct_scanout (
 input logic mem_clk,mem_rst,pixel_clk,pixel_reset_n,
 input logic descriptor_valid,output logic descriptor_ready,
 input logic [63:0] descriptor_generation,input logic [31:0] descriptor_frame_id,input logic [1:0] descriptor_bank,
 output logic presented,error,front_valid,output logic [1:0] front_bank,
 output logic [63:0] front_generation,output logic [31:0] front_frame_id,
 output logic pending_valid,output logic [31:0] presented_count,
 output logic frame_boundary,scanout_drained,
 output logic mem_req_valid,input logic mem_req_ready,output logic [23:0] mem_req_addr,
 input logic mem_rsp_valid,output logic mem_rsp_ready,input logic [15:0] mem_rsp_data,input logic mem_rsp_last,mem_rsp_error,
 output logic [31:0] underruns,memory_errors,
 output logic hsync,vsync,data_enable,output logic [9:0] physical_x,physical_y,output logic [7:0] red,green,blue,
 output logic [31:0] cache_read_commands,cache_read_words,cache_pixel_queries,raster_count
);
 typedef enum logic[1:0] {SELECT_EPOCH,START_EPOCH,RUN_EPOCH} epoch_state_t;
 epoch_state_t state;
 logic [63:0] latest_generation,pending_generation,prepared_generation;
 logic [31:0] pending_frame_id,prepared_frame_id;
 logic [1:0] pending_bank,prepared_bank;
 logic prepared_valid,epoch_playing,old_front_drained,fatal;
 logic descriptor_ok,descriptor_fire,prepared_is_pending,prepared_is_front;
 logic c_desc_valid,c_desc_ready,c_finish_valid,c_finish_ready,c_aborted,c_error;
 
 logic p_valid,p_ready,p_done,p_busy;logic [6:0] p_index,p_done_index,prefetched,consumed;
 logic consume_pending,consume_ready;logic [6:0] consume_index;
 logic pixel_valid,pixel_ready,rgb_valid,rgb_ready,rgb_error;
 logic [9:0] pixel_u,rgb_u;logic [8:0] pixel_v,rgb_v;logic [15:0] rgb;
 logic [3:0] pixel_inflight;
 logic line_req_valid,line_req_ready,line_data_valid,requests_idle;
 logic [23:0] line_req_address;
 logic [15:0] line_data;
 logic line_active,all_lines_done;
 logic [9:0] expected_line,held_u;
 logic [8:0] issued,returned;
 
 
 assign descriptor_ready=!pending_valid&&!mem_rst;
 assign descriptor_ok=descriptor_generation!=0&&descriptor_generation>latest_generation&&descriptor_frame_id!=32'hffffffff&&descriptor_bank<3&&
  (!front_valid||(descriptor_frame_id>front_frame_id&&descriptor_bank!=front_bank));
 assign descriptor_fire=descriptor_valid&&descriptor_ready;
 assign prepared_is_pending=prepared_valid&&pending_valid&&prepared_generation==pending_generation&&prepared_frame_id==pending_frame_id&&prepared_bank==pending_bank;
 assign prepared_is_front=prepared_valid&&front_valid&&prepared_generation==front_generation&&prepared_frame_id==front_frame_id&&prepared_bank==front_bank;
 assign scanout_drained=old_front_drained||presented;
 assign c_desc_valid=state==START_EPOCH&&!mem_rst&&!fatal;
 assign c_finish_valid=state==RUN_EPOCH&&all_lines_done&&!line_active&&!consume_pending&&pixel_inflight==0&&!mem_rst&&!fatal;
 assign p_valid=state==RUN_EPOCH&&!p_busy&&prefetched<90&&int'(prefetched)<int'(consumed)+3&&!mem_rst&&!fatal;
 assign p_index=prefetched;
 assign line_req_ready=epoch_playing&&prepared_is_front&&!line_active&&!consume_pending&&!all_lines_done&&!mem_rst&&!fatal;
 assign pixel_valid=line_active&&issued<480&&!mem_rst&&!fatal;
 assign pixel_u=held_u;assign pixel_v=issued;
 assign rgb_ready=line_active&&!mem_rst&&!fatal;
 assign line_data_valid=rgb_valid&&rgb_ready;
 assign line_data=rgb_error?16'd0:rgb;
 always_ff @(posedge mem_clk)begin
  if(mem_rst)begin
   state<=SELECT_EPOCH;latest_generation<=0;pending_generation<=0;pending_frame_id<=0;pending_bank<=0;
   prepared_generation<=0;prepared_frame_id<=0;prepared_bank<=0;prepared_valid<=0;epoch_playing<=0;old_front_drained<=1;fatal<=0;
   pending_valid<=0;presented<=0;error<=0;front_valid<=0;front_bank<=0;front_generation<=0;front_frame_id<=32'hffffffff;presented_count<=0;
   p_busy<=0;consume_pending<=0;consume_index<=0;line_active<=0;all_lines_done<=0;expected_line<=40;held_u<=0;issued<=0;returned<=0;
   memory_errors<=0;cache_read_commands<=0;cache_read_words<=0;cache_pixel_queries<=0;raster_count<=0;
  end else begin
   presented<=0;error<=0;
   if(mem_req_valid&&mem_req_ready)cache_read_commands<=cache_read_commands+1;
   if(mem_rsp_valid&&mem_rsp_ready)cache_read_words<=cache_read_words+1;
   if(pixel_valid&&pixel_ready)cache_pixel_queries<=cache_pixel_queries+1;
   if(descriptor_fire)begin
    if(!descriptor_ok)error<=1;
    else begin pending_valid<=1;pending_generation<=descriptor_generation;pending_frame_id<=descriptor_frame_id;pending_bank<=descriptor_bank;latest_generation<=descriptor_generation;end
   end
   if(frame_boundary)begin
    if(prepared_valid&&!epoch_playing&&old_front_drained&&requests_idle&&(prepared_is_pending||prepared_is_front))begin
     epoch_playing<=1;old_front_drained<=0;expected_line<=40;
     if(prepared_is_pending)begin front_valid<=1;front_generation<=prepared_generation;front_frame_id<=prepared_frame_id;front_bank<=prepared_bank;pending_valid<=0;presented<=1;presented_count<=presented_count+1;end
    end else if(epoch_playing)begin fatal<=1;error<=1;memory_errors<=memory_errors+1;end
   end
   if(p_valid&&p_ready)p_busy<=1;
   if(p_done)begin
    p_busy<=0;
    if(p_done_index+1'b1!=prefetched)begin fatal<=1;error<=1;memory_errors<=memory_errors+1;end
   end
   if(consume_pending&&consume_ready)consume_pending<=0;
   if(line_req_valid&&line_req_ready)begin
    if(line_req_address!=24'(expected_line)*24'd480||expected_line<40||expected_line>=760)begin fatal<=1;error<=1;memory_errors<=memory_errors+1;end
    line_active<=1;held_u<=expected_line-10'd40;issued<=0;returned<=0;
   end
   if(pixel_valid&&pixel_ready)issued<=issued+1'b1;
   if(line_data_valid)begin
    if(rgb_error||rgb_u!=held_u||rgb_v!=returned||returned>=issued)begin error<=1;memory_errors<=memory_errors+1;end
    returned<=returned+1'b1;
    if(returned==479)begin
     line_active<=0;expected_line<=expected_line+1'b1;
     if(held_u[2:0]==7)begin consume_pending<=1;consume_index<=7'(held_u>>3);end
     if(held_u==719)all_lines_done<=1;
    end
   end
   if(c_error||c_aborted)begin fatal<=1;error<=1;memory_errors<=memory_errors+1;end
   case(state)
    SELECT_EPOCH:if(!fatal&&(pending_valid||front_valid))begin
     if(pending_valid)begin prepared_generation<=pending_generation;prepared_frame_id<=pending_frame_id;prepared_bank<=pending_bank;end
     else begin prepared_generation<=front_generation;prepared_frame_id<=front_frame_id;prepared_bank<=front_bank;end
     state<=START_EPOCH;
    end
    START_EPOCH:if(c_desc_valid&&c_desc_ready)begin prepared_valid<=1;epoch_playing<=0;all_lines_done<=0;consume_pending<=0;p_busy<=0;state<=RUN_EPOCH;end
    RUN_EPOCH:if(c_finish_valid&&c_finish_ready)begin prepared_valid<=0;epoch_playing<=0;old_front_drained<=1;raster_count<=raster_count+1;state<=SELECT_EPOCH;end
    default:state<=SELECT_EPOCH;
   endcase
  end
 end
 cu77_render_bounded_sim renderer(
  .clk(mem_clk),.rst(mem_rst),.abort_i(1'b0),.desc_valid(c_desc_valid),.desc_ready(c_desc_ready),.desc_generation(prepared_generation),.desc_frame_id(prepared_frame_id),.desc_bank(prepared_bank),
  .finish_valid(c_finish_valid),.finish_ready(c_finish_ready),.active(),.aborted(c_aborted),.error(c_error),.error_code(),.active_generation(),.active_frame_id(),
  .prefetch_valid(p_valid),.prefetch_ready(p_ready),.prefetch_index(p_index),.prefetch_done_valid(p_done),.prefetch_done_ready(1'b1),.prefetch_done_index(p_done_index),
  .consume_valid(consume_pending),.consume_ready,.consume_index,.prefetched_count(prefetched),.consumed_count(consumed),
  .mem_req_valid,.mem_req_ready,.mem_req_addr,.mem_rsp_valid,.mem_rsp_ready,.mem_rsp_data,.mem_rsp_last,.mem_rsp_error,
  .pixel_req_valid(pixel_valid),.pixel_req_ready(pixel_ready),.pixel_u,.pixel_v,.rgb_valid,.rgb_ready,.rgb_u,.rgb_v,.rgb_data(rgb),.rgb_error,
  .read_commands(),.read_words(),.pixel_queries(),.cache_misses(),.pixel_inflight);
 cu70_lcd_lines lcd(.pixel_clk,.reset_n(pixel_reset_n),.mem_clk,.mem_reset(mem_rst),.front_valid,.front_buffer(1'b0),.pattern_enable(1'b0),
  .line_req_valid,.line_req_ready,.line_req_address,.line_data_valid,.line_data,.frame_boundary,.underruns,.requests_idle,
  .hsync,.vsync,.data_enable,.physical_x,.physical_y,.red,.green,.blue);
endmodule
