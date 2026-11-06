`timescale 1ns/1ps
// Experimental cache/converter -> frozen native LCD line buffers. Test wrapper,
// not a complete receiver, committed descriptor owner or target CDC signoff.
module cu77_display_sim # (parameter real TAC_NS=2.0)(
 input logic clk,read_clk,pixel_clk,pixel_reset_n,rst,display_rst,abort_i,
 input logic desc_valid,output logic desc_ready,input logic [63:0] desc_generation,input logic [31:0] desc_frame_id,input logic [1:0] desc_bank,
 input logic finish_valid,output logic finish_ready,
 input logic prefetch_valid,output logic prefetch_ready,input logic [6:0] prefetch_index,
 output logic prefetch_done_valid,input logic prefetch_done_ready,output logic [6:0] prefetch_done_index,
 input logic consume_valid,output logic consume_ready,input logic [6:0] consume_index,
 output logic [6:0] prefetched_count,consumed_count,
 output logic active,aborted,cache_error,output logic [7:0] cache_error_code,
 output logic [63:0] active_generation,output logic [31:0] active_frame_id,
 input logic display_desc_valid,output logic display_desc_ready,input logic [63:0] display_desc_generation,input logic [31:0] display_desc_frame_id,
 output logic presented,display_error,front_valid,output logic [63:0] front_generation,output logic [31:0] front_frame_id,
 output logic [31:0] underruns,memory_errors,output logic frame_boundary,scanout_drained,
 output logic hsync,vsync,data_enable,output logic [9:0] physical_x,physical_y,output logic [7:0] red,green,blue,
 input logic aux_req_valid,output logic aux_req_ready,input logic [23:0] aux_req_addr,input logic [127:0] aux_req_burst_data,
 output logic aux_rsp_valid,input logic aux_rsp_ready,output logic aux_rsp_error,
 input logic read_valid,output logic read_ready,input logic [63:0] read_generation,input logic [1:0] read_bank,read_plane,input logic [16:0] read_index,
 output logic read_rsp_valid,input logic read_rsp_ready,output logic [511:0] read_rsp_pixels,output logic read_rsp_error,
 input logic write_valid,output logic write_ready,input logic [63:0] write_generation,input logic [1:0] write_bank,write_plane,input logic [16:0] write_index,input logic [511:0] write_pixels,
 output logic write_done_valid,input logic write_done_ready,output logic write_done_error,
 output logic [31:0] read_commands,read_words,pixel_queries,cache_misses,model_reads,model_writes,model_write_commands,model_write_beats,
 output logic [23:0] model_last_write_address,output logic [15:0] model_last_write_data,
 output logic adapter_error,output logic [31:0] pixels_inflight
);
 logic cache_desc_ready,cache_finish_ready,req_valid,req_ready,rsp_valid,rsp_ready,rsp_last,rsp_error;
 logic [23:0] req_addr;logic [15:0] rsp_data;
 logic pixel_req_valid,pixel_req_ready,pixel_rsp_valid,pixel_rsp_ready,pixel_rsp_error;
 logic [9:0] pixel_u,pixel_rsp_u;logic [8:0] pixel_v,pixel_rsp_v;
 logic [7:0] pixel_y,cb00,cb10,cb01,cb11,cr00,cr10,cr01,cr11;logic pixel_hud_hit;logic [15:0] pixel_hud;
 logic rgb_valid,rgb_ready,rgb_error;logic[9:0]rgb_u;logic[8:0]rgb_v;logic[15:0]rgb;
 logic v_req_valid,v_req_ready,v_rsp_valid,v_rsp_ready;logic[23:0]v_req_addr;logic v_rsp_last,v_rsp_error;
 logic adapter_active;logic[23:0] virtual_address;logic[3:0]issued,returned;
 logic [23:0] offset;logic[9:0]coded_u;logic[8:0]coded_v;
 assign offset=virtual_address-24'hc00000;
 assign coded_u=10'(offset/24'd480)-10'd40;assign coded_v=9'(offset%24'd480);
 assign desc_ready=cache_desc_ready&&pixels_inflight==0&&!adapter_active;
 assign finish_ready=cache_finish_ready&&pixels_inflight==0&&!adapter_active;
 assign v_req_ready=!adapter_active&&!rst;
 assign pixel_req_valid=adapter_active&&issued<8&&!rst&&!abort_i;
 assign pixel_u=coded_u;assign pixel_v=coded_v+9'(issued);
 assign v_rsp_valid=adapter_active&&rgb_valid&&!rst;
 assign rgb_ready=adapter_active&&v_rsp_ready&&!rst;
 assign v_rsp_last=returned==7;
 assign v_rsp_error=rgb_error||rgb_u!=coded_u||rgb_v!=coded_v+9'(returned);
 always_ff @(posedge clk)begin
  if(rst||abort_i||display_rst)begin adapter_active<=0;virtual_address<=0;issued<=0;returned<=0;adapter_error<=0;pixels_inflight<=0;end
  else begin
   case({pixel_req_valid&&pixel_req_ready,rgb_valid&&rgb_ready})
    2'b10:pixels_inflight<=pixels_inflight+1;
    2'b01:pixels_inflight<=pixels_inflight-1;
    default:begin end
   endcase
   if(v_req_valid&&v_req_ready)begin
    adapter_active<=1;virtual_address<=v_req_addr;issued<=0;returned<=0;
    if(v_req_addr<24'hc00000+24'd19200||v_req_addr>=24'hc00000+24'd364800||v_req_addr[2:0]!=0)adapter_error<=1;
   end
   if(pixel_req_valid&&pixel_req_ready)issued<=issued+1;
   if(rgb_valid&&rgb_ready)begin
    if(v_rsp_error||returned>=issued)adapter_error<=1;
    returned<=returned+1;
    if(returned==7)adapter_active<=0;
   end
  end
 end
 cu77_direct_cache cache(
  .clk,.rst,.abort_i,.desc_valid(desc_valid&&pixels_inflight==0&&!adapter_active),.desc_ready(cache_desc_ready),.desc_generation,.desc_frame_id,.desc_bank,
  .finish_valid(finish_valid&&pixels_inflight==0&&!adapter_active),.finish_ready(cache_finish_ready),
  .active,.aborted,.error(cache_error),.error_code(cache_error_code),.active_generation,.active_frame_id,
  .prefetch_valid,.prefetch_ready,.prefetch_index,.prefetch_done_valid,.prefetch_done_ready,.prefetch_done_index,
  .consume_valid,.consume_ready,.consume_index,.prefetched_count,.consumed_count,
  .mem_req_valid(req_valid),.mem_req_ready(req_ready),.mem_req_addr(req_addr),.mem_rsp_valid(rsp_valid),.mem_rsp_ready(rsp_ready),.mem_rsp_data(rsp_data),.mem_rsp_last(rsp_last),.mem_rsp_error(rsp_error),
  .pixel_req_valid,.pixel_req_ready,.pixel_u,.pixel_v,.pixel_rsp_valid,.pixel_rsp_ready,.pixel_rsp_u,.pixel_rsp_v,
  .pixel_y,.cb00,.cb10,.cb01,.cb11,.cr00,.cr10,.cr01,.cr11,.pixel_hud_hit,.pixel_hud,.pixel_rsp_error,
  .read_commands,.read_words,.pixel_queries,.cache_misses);
 cu77_yuv_rgb convert(.clk,.rst,.abort_i(abort_i||display_rst),.in_valid(pixel_rsp_valid),.in_ready(pixel_rsp_ready),.in_u(pixel_rsp_u),.in_v(pixel_rsp_v),.in_y(pixel_y),
  .in_cb00(cb00),.in_cb10(cb10),.in_cb01(cb01),.in_cb11(cb11),.in_cr00(cr00),.in_cr10(cr10),.in_cr01(cr01),.in_cr11(cr11),
  .in_hud_hit(pixel_hud_hit),.in_hud(pixel_hud),.in_error(pixel_rsp_error),.out_valid(rgb_valid),.out_ready(rgb_ready),.out_u(rgb_u),.out_v(rgb_v),.out_rgb(rgb),.out_error(rgb_error));
 cu71_scanout scanout(.mem_clk(clk),.mem_rst(rst||display_rst),.pixel_clk,.pixel_reset_n,.descriptor_valid(display_desc_valid),.descriptor_ready(display_desc_ready),
  .descriptor_generation(display_desc_generation),.descriptor_frame_id(display_desc_frame_id),.descriptor_slot(1'b0),.presented,.error(display_error),.front_valid,.front_slot(),.front_generation,.front_frame_id,
  .pending_valid(),.presented_count(),.frame_boundary,.scanout_drained,.lcd_req_valid(v_req_valid),.lcd_req_ready(v_req_ready),.lcd_req_addr(v_req_addr),
  .lcd_rsp_valid(v_rsp_valid),.lcd_rsp_ready(v_rsp_ready),.lcd_rsp_data(rgb),.lcd_rsp_last(v_rsp_last),.lcd_rsp_error(v_rsp_error),.underruns,.memory_errors,
  .hsync,.vsync,.data_enable,.physical_x,.physical_y,.red,.green,.blue);
 wire[12:0]sdram_a;wire[1:0]sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 cu74_memory_system #(.POWERUP_CYCLES(20)) memory(.clk,.read_clk,.rst,.abort_i(1'b0),.aux_abort_i(1'b0),
  .read_valid,.read_ready,.read_generation,.read_bank,.read_plane,.read_index,.read_rsp_valid,.read_rsp_ready,.read_rsp_generation(),.read_rsp_bank(),.read_rsp_plane(),.read_rsp_index(),.read_rsp_pixels,.read_rsp_error,
  .write_valid,.write_ready,.write_generation,.write_bank,.write_plane,.write_index,.write_pixels,.write_done_valid,.write_done_ready,.write_done_generation(),.write_done_bank(),.write_done_plane(),.write_done_index(),.write_done_error,.tile_busy(),.tile_aborted(),
  .aux_req_valid,.aux_req_ready,.aux_req_write(1'b1),.aux_req_addr,.aux_req_data(16'd0),.aux_req_read_burst(1'b0),.aux_rsp_burst_data(),
  .aux_req_burst(1'b1),.aux_req_burst_data,.aux_req_byte_enable(16'hffff),.aux_rsp_valid,.aux_rsp_ready,.aux_rsp_data(),.aux_rsp_error,.aux_busy(),.aux_aborted(),
  .lcd_req_valid(req_valid),.lcd_req_ready(req_ready),.lcd_req_addr(req_addr),.lcd_rsp_valid(rsp_valid),.lcd_rsp_ready(rsp_ready),.lcd_rsp_data(rsp_data),.lcd_rsp_last(rsp_last),.lcd_rsp_error(rsp_error),.lcd_busy(),
  .cache_hits(),.cache_misses(),.completed_reads(),.completed_writes(),.p0_cache_hits(),.p0_cache_misses(),.p0_row_reads(),.p0_wait_cycles(),.p0_service_cycles(),.p1_cache_hits(),.p1_cache_misses(),.p0_read_wait_cycles(),.p0_read_service_cycles(),
  .sdram_a,.sdram_bs,.sdram_cke,.sdram_cs_n,.sdram_dq,.sdram_clk,.sdram_ras_n,.sdram_cas_n,.sdram_we_n,.sdram_ldqm,.sdram_udqm,.idle());
 cu72_sdram_model #(.T_AC_NS(TAC_NS)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 assign model_last_write_address=model.last_write_address;assign model_last_write_data=model.last_write_data;
 assign model_reads=32'(model.reads);assign model_writes=32'(model.writes);assign model_write_commands=32'(model.write_commands);assign model_write_beats=32'(model.write_bus_beats);
endmodule
