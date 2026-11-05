`timescale 1ns/1ps
module tb_natural;
`include "top-harness.svh"
 reg[9:0]xd[0:2],yd[0:2];reg ded[0:2];reg[23:0]rgbd[0:2];integer d,warm=0;
 reg observing=0;reg[23:0]want;
 always @(posedge dut.pclk)begin
  xd[0]<=dut.px;yd[0]<=dut.py;ded[0]<=dut.de;rgbd[0]<={dut.red,dut.green,dut.blue};
  for(d=1;d<3;d=d+1)begin xd[d]<=xd[d-1];yd[d]<=yd[d-1];ded[d]<=ded[d-1];rgbd[d]<=rgbd[d-1];end
  warm<=warm+1;
 end
 always @(negedge dut.pclk)if(observing&&warm>10)begin
  want=ded[2]?(xd[2]<2&&yd[2]>=12&&yd[2]<14?24'hff0000:rgbd[2]):24'd0;
  if(de!==ded[2]||{r,g,b}!==want)$fatal(1,"natural overlay/RGB pipeline x%0d y%0d got%h expected%h",xd[2],yd[2],{r,g,b},want);
 end
 task capture_frame(input integer htotal,input integer vtotal,input integer margin_value);
 integer n,active_count,hs_count,vs_count,source_row,bar;reg[23:0]base_expected;begin
  active_count=0;hs_count=0;vs_count=0;
  repeat(20)@(negedge dut.pclk);observing=1;
  for(n=0;n<htotal*vtotal;n=n+1)begin
   @(negedge dut.pclk);active_count=active_count+dut.de;hs_count=hs_count+dut.hs;vs_count=vs_count+dut.vs;
   if(dut.de)begin
    source_row=dut.py-margin_value;
    bar=source_row<0||source_row>=720?7:source_row/90;
    case(bar)
     0:base_expected=24'hffffff;1:base_expected=24'hffff00;2:base_expected=24'h00ffff;3:base_expected=24'h00ff00;
     4:base_expected=24'hff00ff;5:base_expected=24'hff0000;6:base_expected=24'h0000ff;default:base_expected=0;
    endcase
    if({dut.red,dut.green,dut.blue}!==base_expected)$fatal(1,"native bars margin%0d row%0d got%h expected%h",margin_value,dut.py,{dut.red,dut.green,dut.blue},base_expected);
   end
  end
  observing=0;
  if(active_count!=384000||hs_count!=dut.timing_hsync*vtotal||vs_count!=dut.timing_vsync*htotal)$fatal(1,"natural frame geometry active%0d hs%0d vs%0d",active_count,hs_count,vs_count);
  $display("NATURAL_FRAME_PASS htotal=%0d vtotal=%0d active=%0d margin=%0d overlay_three_stages=1",htotal,vtotal,active_count,margin_value);$fflush();
 end endtask
 initial begin
  if(!$test$plusargs("natural"))$fatal(1,"natural test must not force frame origins");
  wait(!dut.rst100[3]&&!dut.rst200[3]&&!dut.rstpixel[3]);
  wait(dut.margin.pixel_pending&&dut.timing.pixel_pending);@(posedge dut.lcd_frame_origin);#1000;ready();
  write_mode(32'h03000000,4,16,0,32'hfc00);capture_frame(541,834,20);
  write_reg('h084,80);write_reg('h09c,1);
  if(dut.display_margin!=20||dut.timing_htotal!=541||dut.timing_vtotal!=834)$fatal(1,"natural controls applied midframe");
  @(posedge dut.lcd_frame_origin);#1000;ready();
  if(dut.display_margin!=80||dut.timing_htotal!=605||dut.timing_vtotal!=809)$fatal(1,"natural controls did not apply on origin");
  capture_frame(605,809,80);
  $display("AKD1_NATURAL_LCD_PASS frames=2 natural_origins=1 native_bars_not_compute=1 margins20_80=1 porch_profiles0_1=1 overlay=1 inactive_SDRAM=1");$finish;
 end
 initial begin #150000000;$fatal(1,"natural LCD timeout");end
endmodule
