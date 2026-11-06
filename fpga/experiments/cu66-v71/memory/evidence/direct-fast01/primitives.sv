`timescale 1ns/1ps
// Functional primitive subset for this top's constant reset/enable clock paths.
// No PLL jitter, IO delay, metastability or board/panel analog behavior modeled.
module IBUF(input I,output O);assign O=I;endmodule
module BUFG(input I,output O);assign O=I;endmodule
module IOBUF(input I,input T,inout IO,output O);assign IO=T?1'bz:I;assign O=IO;endmodule
module OBUFT(input I,input T,output O);assign O=T?1'bz:I;endmodule
module ODDR #(parameter DDR_CLK_EDGE="OPPOSITE_EDGE",parameter INIT=1'b0)(input C,CE,D1,D2,R,S,output reg Q=INIT);
 reg d2_hold=0;
 always @(posedge C)begin
  if(R)begin Q<=0;d2_hold<=0;end
  else if(S)begin Q<=1;d2_hold<=1;end
  else if(CE)begin Q<=D1;d2_hold<=D2;end
 end
 always @(negedge C)begin
  if(R)Q<=0;else if(S)Q<=1;else if(CE)Q<=(DDR_CLK_EDGE=="SAME_EDGE")?d2_hold:D2;
 end
endmodule
module PLLE2_BASE #(
 parameter real CLKIN1_PERIOD=20.0,parameter integer CLKFBOUT_MULT=20,DIVCLK_DIVIDE=1,
 parameter integer CLKOUT0_DIVIDE=5,CLKOUT1_DIVIDE=10,CLKOUT2_DIVIDE=10,
 parameter real CLKOUT2_PHASE=279.0
)(input CLKIN1,CLKFBIN,PWRDWN,RST,output CLKFBOUT,output reg CLKOUT0=0,CLKOUT1=0,CLKOUT2=0,LOCKED=0);
 assign CLKFBOUT=CLKIN1;
 initial begin #100;LOCKED=1;end
 always #(CLKIN1_PERIOD*DIVCLK_DIVIDE*CLKOUT0_DIVIDE/CLKFBOUT_MULT/2.0)CLKOUT0=~CLKOUT0;
 always #(CLKIN1_PERIOD*DIVCLK_DIVIDE*CLKOUT1_DIVIDE/CLKFBOUT_MULT/2.0)CLKOUT1=~CLKOUT1;
 initial begin #(CLKIN1_PERIOD*DIVCLK_DIVIDE*CLKOUT2_DIVIDE/CLKFBOUT_MULT*CLKOUT2_PHASE/360.0);
  forever #(CLKIN1_PERIOD*DIVCLK_DIVIDE*CLKOUT2_DIVIDE/CLKFBOUT_MULT/2.0)CLKOUT2=~CLKOUT2;
 end
endmodule
module MMCME2_BASE #(
 parameter real CLKIN1_PERIOD=20.0,CLKFBOUT_MULT_F=56.375,CLKOUT0_DIVIDE_F=32.0,
 parameter integer DIVCLK_DIVIDE=3
)(input CLKIN1,CLKFBIN,PWRDWN,RST,output CLKFBOUT,output reg CLKOUT0=0,LOCKED=0);
 assign CLKFBOUT=CLKIN1;
 initial begin #100;LOCKED=1;end
 always #(CLKIN1_PERIOD*DIVCLK_DIVIDE*CLKOUT0_DIVIDE_F/CLKFBOUT_MULT_F/2.0)CLKOUT0=~CLKOUT0;
endmodule
