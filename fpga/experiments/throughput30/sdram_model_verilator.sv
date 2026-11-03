`timescale 1ns/1ps
// Verification-only variant of fpga/sim/sdram_model.sv. The device-clock delay
// uses an edge-triggered NBA instead of a delayed continuous assignment to avoid
// excessive event rescheduling in Verilator 5.020. This is a separate model;
// same cycle counts on the test trace are evidence, not general equivalence.
// The simulated clock edges are separated by more than CLOCK_FLIGHT_NS;
// this bounded functional model is not vendor timing signoff.
module sdram_model #(parameter real T_AC_NS=2.0, CLOCK_FLIGHT_NS=4.0)(input wire clk,input wire[12:0]a,input wire[1:0]ba,input wire[1:0]cke,cs,
 input wire ras,cas,we,ldqm,udqm,inout wire[15:0]dq);
 reg[15:0]mem[0:1048575];reg[12:0]rows[0:3];reg[3:0]opened=0;
 reg drive=0;reg[15:0]outdata;assign dq=drive ? outdata:16'bz;
 integer latency=0,left=0,readaddr=0,refreshes=0,mrs=0,writes=0;
 integer lastact[0:3],lastpre[0:3],cycle=0,i;
 initial for(i=0;i<4;i=i+1)begin lastact[i]=-100;lastpre[i]=-100;end
 // Representative FPGA forwarded-clock pad insertion, separately from tAC.
 // The actual pin round trip is qualified by routed external timing reports.
 reg device_clock;always @(clk) device_clock <= #(CLOCK_FLIGHT_NS) clk;
 always @(posedge device_clock)if(cke[0])begin
  cycle=cycle+1;
  if(latency>0)begin
   latency=latency-1;
   if(latency==0)begin outdata<=#(T_AC_NS) mem[readaddr];drive<=#(T_AC_NS) 1;readaddr=readaddr+1;left=7;end
  end else if(left>0)begin outdata<=#(T_AC_NS) mem[readaddr];readaddr=readaddr+1;left=left-1;end
  else drive<=#(T_AC_NS) 0;
  if(!cs[0])case({ras,cas,we})
   3'b011:begin
    if(opened[ba])$fatal(1,"ACT on open bank");
    if(cycle-lastpre[ba]<2)$fatal(1,"tRP violated");
    opened[ba]=1;rows[ba]=a;lastact[ba]=cycle;
   end
   3'b010:begin
    if(!a[10]&&cycle-lastact[ba]<5)$fatal(1,"tRAS violated");
    if(a[10])begin opened=0;for(i=0;i<4;i=i+1)lastpre[i]=cycle;end
    else begin opened[ba]=0;lastpre[ba]=cycle;end
   end
   3'b100:begin
    if(!opened[ba]||cycle-lastact[ba]<2)$fatal(1,"write tRCD violated");
    if(ldqm||udqm)$fatal(1,"bad write mask");
    mem[{ba,rows[ba],a[8:0]}]=dq;writes=writes+1;
   end
   3'b101:begin
    if(!opened[ba]||cycle-lastact[ba]<2)$fatal(1,"read tRCD violated");
    if(a[2:0]!=0)$fatal(1,"unaligned burst test");
    readaddr={ba,rows[ba],a[8:0]};latency=3;
   end
   3'b001:begin if(opened!=0)$fatal(1,"refresh openbank");refreshes=refreshes+1;end
   3'b000:begin if(a!==13'h233)$fatal(1,"bad mode %x",a);mrs=mrs+1;end
  endcase
 end
endmodule
