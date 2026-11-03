`timescale 1ns/1ps
// Isolated controller handshake timing. No SDRAM model/data checking, refresh,
// client arbiter or physical I/O timing. Same-bank row changes are generated.
module tb_sdram_rowhit;
 reg clk=0;always #5 clk=~clk;
 reg reset=1;integer cycle=0,n0=0,n1=0,last0=0,last1=0;integer w0=0,r0=0,w1=0,r1=0;
 integer xw0=0,xr0=0,xw1=0,xr1=0;
 integer act0=0,cmdw0=0,cmdr0=0,act1=0,cmdw1=0,cmdr1=0;
 wire ready0,ready1;tri [15:0] dq0,dq1;
 wire [12:0] a0,a1;wire[1:0] b0,b1,cke0,cke1,cs0,cs1;
 wire clk0,clk1,ras0,ras1,cas0,cas1,we0,we1,ld0,ld1,ud0,ud1;
 wire rv0,rv1,idle0,idle1;wire[15:0] rd0,rd1;
 moonshine_sdram #(.POWERUP_CYCLES(1),.REFRESH_CYCLES(60000)) baseline(
  .clk(clk),.read_clk(clk),.reset(reset),.request_valid(!reset && n0<24),.request_ready(ready0),
  .request_write(n0<6 || (n0>=12 && n0<18)),.request_address((n0>=12 && n0[0]) ? 24'd512 : 24'd0),.request_data(16'h1234),
  .response_valid(rv0),.response_data(rd0),.idle(idle0),
  .sdram_a(a0),.sdram_bs(b0),.sdram_dq(dq0),.sdram_clk(clk0),.sdram_cke(cke0),.sdram_cs_n(cs0),
  .sdram_ras_n(ras0),.sdram_cas_n(cas0),.sdram_we_n(we0),.sdram_ldqm(ld0),.sdram_udqm(ud0));
 moonshine_sdram_burst #(.POWERUP_CYCLES(1),.REFRESH_CYCLES(60000)) burst(
  .clk(clk),.read_clk(clk),.reset(reset),.request_valid(!reset && n1<24),.request_ready(ready1),
  .request_write(n1<6 || (n1>=12 && n1<18)),.request_address((n1>=12 && n1[0]) ? 24'd512 : 24'd0),.request_burst_data(128'h1234),
  .response_valid(rv1),.response_data(rd1),.idle(idle1),
  .sdram_a(a1),.sdram_bs(b1),.sdram_dq(dq1),.sdram_clk(clk1),.sdram_cke(cke1),.sdram_cs_n(cs1),
  .sdram_ras_n(ras1),.sdram_cas_n(cas1),.sdram_we_n(we1),.sdram_ldqm(ld1),.sdram_udqm(ud1));
 always @(posedge clk)begin
  cycle<=cycle+1;
  if(!reset && !cs0[0])begin
   if(!ras0 && cas0 && we0)begin if(a0>1 || b0!=0)$fatal(1,"baseline unexpected activate");act0<=act0+1;end
   if(ras0 && !cas0)begin
    if(a0!=0 || b0!=0)$fatal(1,"baseline nonzero column");
    if(we0)cmdr0<=cmdr0+1;else cmdw0<=cmdw0+1;
   end
  end
  if(!reset && !cs1[0])begin
   if(!ras1 && cas1 && we1)begin if(a1>1 || b1!=0)$fatal(1,"burst unexpected activate");act1<=act1+1;end
   if(ras1 && !cas1)begin
    if(a1!=0 || b1!=0)$fatal(1,"burst nonzero column");
    if(we1)cmdr1<=cmdr1+1;else cmdw1<=cmdw1+1;
   end
  end
  if(!reset && ready0 && n0<24)begin
   if(n0>=2 && n0<6)begin if(cycle-last0!=6)$fatal(1,"baseline write gap %0d",cycle-last0);w0<=w0+1;end
   if(n0>=7 && n0<12)begin if(cycle-last0!=15)$fatal(1,"baseline read gap %0d",cycle-last0);r0<=r0+1;end
   if(n0>=14 && n0<18)begin if(cycle-last0!=14)$fatal(1,"baseline row-switch write %0d",cycle-last0);xw0<=xw0+1;end
   if(n0>=19)begin if(cycle-last0!=23)$fatal(1,"baseline row-switch read %0d",cycle-last0);xr0<=xr0+1;end
   last0<=cycle;n0<=n0+1;
  end
  if(!reset && ready1 && n1<24)begin
   if(n1>=2 && n1<6)begin if(cycle-last1!=13)$fatal(1,"burst write gap %0d",cycle-last1);w1<=w1+1;end
   if(n1>=7 && n1<12)begin if(cycle-last1!=15)$fatal(1,"burst read gap %0d",cycle-last1);r1<=r1+1;end
   if(n1>=14 && n1<18)begin if(cycle-last1!=21)$fatal(1,"burst row-switch write %0d",cycle-last1);xw1<=xw1+1;end
   if(n1>=19)begin if(cycle-last1!=23)$fatal(1,"burst row-switch read %0d",cycle-last1);xr1<=xr1+1;end
   last1<=cycle;n1<=n1+1;
  end
 end
 initial begin
  repeat(3)@(negedge clk);reset=0;
  wait(n0==24 && n1==24);repeat(30)@(negedge clk);
  if(w0!=4||r0!=5||w1!=4||r1!=5)$fatal(1,"missing samples");
  if(xw0!=4||xr0!=5||xw1!=4||xr1!=5)$fatal(1,"missing row-switch samples");
  if(act0!=12||cmdw0!=12||cmdr0!=12||act1!=12||cmdw1!=12||cmdr1!=12)$fatal(1,"command counts %0d %0d %0d %0d %0d %0d",act0,cmdw0,cmdr0,act1,cmdw1,cmdr1);
  $display("SDRAM_TIMING_PASS hit_baseline=6,15 hit_burst=13,15 switch_baseline=14,23 switch_burst=21,23 write_samples=4 read_samples=5 activate=12 writes=12 reads=12");$finish;
 end
 initial begin #100000;$fatal(1,"watchdog");end
endmodule
