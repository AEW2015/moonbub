// Exact CU66 bilinear/Q8 color conversion. Three elastic stages, II=1.
module cu77_yuv_rgb (
 input logic clk,rst,abort_i,
 input logic in_valid,output logic in_ready,
 input logic [9:0] in_u,input logic [8:0] in_v,
 input logic [7:0] in_y,in_cb00,in_cb10,in_cb01,in_cb11,in_cr00,in_cr10,in_cr01,in_cr11,
 input logic in_hud_hit,input logic [15:0] in_hud,input logic in_error,
 output logic out_valid,input logic out_ready,
 output logic [9:0] out_u,output logic [8:0] out_v,
 output logic [15:0] out_rgb,output logic out_error
);
 logic v0,v1,v2,r0,r1,r2;
 logic [9:0] u0,u1,u2;logic [8:0] vv0,vv1,vv2;
 logic [7:0] y0;logic signed[8:0] cb0,cr0;
 logic h0,h1,e0,e1,e2;logic[15:0] hud0,hud1,rgb2;
 logic signed[18:0] red1,green1,blue1;
 logic signed[18:0] red_calc,green_calc,blue_calc;

 function automatic logic signed[8:0] interp(input logic[7:0] a,b,c,d,input logic oddx,oddy);
  integer top,bottom;
  begin
   top=int'(a);bottom=int'(c);
   if(oddx)begin top=(top+int'(b)+1)/2;bottom=(bottom+int'(d)+1)/2;end
   if(oddy)top=(top+bottom+1)/2;
   interp=9'(top-128);
  end
 endfunction
 function automatic logic[4:0] clamp5(input logic signed[18:0] value);
  if(value<0)clamp5=0;else if(value>255)clamp5=31;else clamp5=5'(value>>>3);
 endfunction
 function automatic logic[5:0] clamp6(input logic signed[18:0] value);
  if(value<0)clamp6=0;else if(value>255)clamp6=63;else clamp6=6'(value>>>2);
 endfunction
 always_comb begin
  r2=!v2||out_ready;r1=!v1||r2;r0=!v0||r1;
  in_ready=r0&&!rst&&!abort_i;out_valid=v2&&!rst&&!abort_i;
  out_u=u2;out_v=vv2;out_rgb=rgb2;out_error=e2;
  red_calc=19'($signed({1'b0,y0}))+((19'($signed(cr0))*19'sd359+19'sd128)>>>8);
  green_calc=19'($signed({1'b0,y0}))-((19'($signed(cb0))*19'sd88+19'($signed(cr0))*19'sd183+19'sd128)>>>8);
  blue_calc=19'($signed({1'b0,y0}))+((19'($signed(cb0))*19'sd454+19'sd128)>>>8);

 end
 always_ff @(posedge clk)begin
  if(rst||abort_i)begin
   v0<=0;v1<=0;v2<=0;u0<=0;u1<=0;u2<=0;vv0<=0;vv1<=0;vv2<=0;
   y0<=0;cb0<=0;cr0<=0;h0<=0;h1<=0;e0<=0;e1<=0;e2<=0;hud0<=0;hud1<=0;rgb2<=0;red1<=0;green1<=0;blue1<=0;
  end else begin
   if(r0)begin
    v0<=in_valid;
    if(in_valid)begin
     u0<=in_u;vv0<=in_v;y0<=in_y;
     cb0<=interp(in_cb00,in_cb10,in_cb01,in_cb11,in_u[0],in_v[0]);
     cr0<=interp(in_cr00,in_cr10,in_cr01,in_cr11,in_u[0],in_v[0]);
     h0<=in_hud_hit;hud0<=in_hud;e0<=in_error;
    end
   end
   if(r1)begin
    v1<=v0;
    if(v0)begin u1<=u0;vv1<=vv0;h1<=h0;hud1<=hud0;e1<=e0;red1<=red_calc;green1<=green_calc;blue1<=blue_calc;end
   end
   if(r2)begin
    v2<=v1;
    if(v1)begin u2<=u1;vv2<=vv1;e2<=e1;rgb2<=h1?hud1:{clamp5(red1),clamp6(green1),clamp5(blue1)};end
   end
  end
 end
endmodule
