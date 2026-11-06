// Exact native YUV420 bilinear/color/HUD path, throughput one pixel/clock.
// Five owned data stages; no backpressure. The caller supplies one aligned
// raw Y/2x2-Cb/2x2-Cr neighborhood and exact HUD word per valid input.
`timescale 1ns/1ps
`default_nettype none
module cu71_yuv_pixel_pipe(
 input wire clk,rst,
 input wire in_valid,input wire[31:0]in_tag,
 input wire[7:0]in_y,in_cb_t0,in_cb_t1,in_cb_b0,in_cb_b1,
 input wire[7:0]in_cr_t0,in_cr_t1,in_cr_b0,in_cr_b1,
 input wire in_x_odd,in_y_odd,in_hud_hit,input wire[15:0]in_hud_word,
 output wire out_valid,output wire[31:0]out_tag,output wire[15:0]out_rgb,
 output wire busy
);
 reg[4:0]valid;
 reg[31:0]tag0,tag1,tag2,tag3,tag4;
 reg[3:0]hud_hit;
 reg[15:0]hud0,hud1,hud2,hud3;
 reg[7:0]y1,y2,y3,cb_top1,cb_bottom1,cr_top1,cr_bottom1;
 reg y_odd1;
 reg signed[8:0]cb2,cr2;
 reg signed[18:0]red3,blue3,green_cb3,green_cr3;
 reg signed[10:0]red4,green4,blue4;
 reg[15:0]rgb5;
 function automatic[7:0]average_byte(input[7:0]a,b,input blend);
  reg[8:0]unused_sum_lsb;
  begin unused_sum_lsb={1'b0,a}+{1'b0,b}+9'd1;average_byte=blend?unused_sum_lsb[8:1]:a;end
 endfunction
 function automatic[7:0]clip(input signed[10:0]n);
  if(n<0)clip=0;else if(n>255)clip=255;else clip=n[7:0];
 endfunction
 wire[7:0]r8=clip(red4),g8=clip(green4),b8=clip(blue4);
 assign out_valid=valid[4];assign out_tag=tag4;
 assign out_rgb=out_valid?rgb5:16'd0;
 assign busy=|valid;
 // Only validity is reset. Data cannot be published until all five stages
 // have been overwritten by a valid predecessor after coordinated reset.
 always @(posedge clk)begin
  if(rst)valid<=0;else valid<={valid[3:0],in_valid};
  tag0<=in_tag;tag1<=tag0;tag2<=tag1;tag3<=tag2;tag4<=tag3;
  hud_hit<={hud_hit[2:0],in_hud_hit};
  hud0<=in_hud_word;hud1<=hud0;hud2<=hud1;hud3<=hud2;
  y1<=in_y;y2<=y1;y3<=y2;y_odd1<=in_y_odd;
  cb_top1<=average_byte(in_cb_t0,in_cb_t1,in_x_odd);
  cb_bottom1<=average_byte(in_cb_b0,in_cb_b1,in_x_odd);
  cr_top1<=average_byte(in_cr_t0,in_cr_t1,in_x_odd);
  cr_bottom1<=average_byte(in_cr_b0,in_cr_b1,in_x_odd);
  cb2<=$signed({1'b0,average_byte(cb_top1,cb_bottom1,y_odd1)})-9'sd128;
  cr2<=$signed({1'b0,average_byte(cr_top1,cr_bottom1,y_odd1)})-9'sd128;
  red3<=cr2*10'sd359;blue3<=cb2*10'sd454;
  green_cb3<=cb2*10'sd88;green_cr3<=cr2*10'sd183;
  red4<=11'($signed({1'b0,y3})+((red3+19'sd128)>>>8));
  green4<=11'($signed({1'b0,y3})-((green_cb3+green_cr3+19'sd128)>>>8));
  blue4<=11'($signed({1'b0,y3})+((blue3+19'sd128)>>>8));
  rgb5<=hud_hit[3]?hud3:{r8[7:3],g8[7:2],b8[7:3]};
 end
endmodule
`default_nettype wire
