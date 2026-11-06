`timescale 1ns/1ps
module cu71_cache_pixel_test(
 input wire clk,rst,
 input wire wr_valid,wr_allow,wr_context,wr_bank,input wire[1:0]wr_kind,
 input wire[8:0]wr_row,input wire[63:0]wr_data,input wire[14:0]wr_hud_index,
 input wire[15:0]wr_hud_word,output wire wr_error,
 input wire front_valid,front_context,render_live,render_context,input wire[9:0]render_u,
 input wire rd_valid,rd_context,input wire[9:0]rd_u,input wire[8:0]rd_v,
 input wire rd_hud_hit,input wire[14:0]rd_hud_index,input wire[31:0]rd_tag,
 output wire out_valid,output wire[31:0]out_tag,output wire[15:0]out_rgb,
 output wire read_error,busy
);
 wire cache_valid,cache_error,hud_hit,x_odd,y_odd;
 wire[31:0]cache_tag;
 wire[7:0]Y,cb_t0,cb_t1,cb_b0,cb_b1,cr_t0,cr_t1,cr_b0,cr_b1;
 wire[15:0]hud_word;
 cu71_direct_cache cache(.clk,.rst,.wr_valid,.wr_allow,.wr_context,.wr_bank,.wr_kind,.wr_row,.wr_data,.wr_hud_index,.wr_hud_word,.wr_error,
 .front_valid,.front_context,.render_live,.render_context,.render_u,
 .rd_valid,.rd_context,.rd_u,.rd_v,.rd_hud_hit,.rd_hud_index,.rd_tag,
 .out_valid(cache_valid),.out_error(cache_error),.out_tag(cache_tag),.out_y(Y),
 .out_cb_t0(cb_t0),.out_cb_t1(cb_t1),.out_cb_b0(cb_b0),.out_cb_b1(cb_b1),
 .out_cr_t0(cr_t0),.out_cr_t1(cr_t1),.out_cr_b0(cr_b0),.out_cr_b1(cr_b1),
 .out_x_odd(x_odd),.out_y_odd(y_odd),.out_hud_word(hud_word),.out_hud_hit(hud_hit));
 assign read_error=cache_error;
 wire pixel_busy;
 assign busy=cache_valid||pixel_busy;
 cu71_yuv_pixel_pipe pixel(.clk,.rst,.in_valid(cache_valid&&!cache_error),.in_tag(cache_tag),.in_y(Y),
 .in_cb_t0(cb_t0),.in_cb_t1(cb_t1),.in_cb_b0(cb_b0),.in_cb_b1(cb_b1),
 .in_cr_t0(cr_t0),.in_cr_t1(cr_t1),.in_cr_b0(cr_b0),.in_cr_b1(cr_b1),
 .in_x_odd(x_odd),.in_y_odd(y_odd),.in_hud_hit(hud_hit),.in_hud_word(hud_word),
 .out_valid,.out_tag,.out_rgb,.busy(pixel_busy));
endmodule
