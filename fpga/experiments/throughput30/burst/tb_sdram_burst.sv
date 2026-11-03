`timescale 1ns/1ps
module tb_sdram_burst;
 reg clk=0,reset=1,valid=0,write=1; always #5 clk=~clk;
 wire read_clk;assign #2.75 read_clk=~clk;
 reg [23:0] addr=0;reg [127:0] payload=0;
 wire ready,rsp_valid,idle;wire[15:0]rsp_data,dq;wire[12:0]a;
 wire[1:0]ba,cke,cs;wire sclk,ras,cas,we,ldqm,udqm;
 moonshine_sdram_burst #(.POWERUP_CYCLES(20),.REFRESH_CYCLES(70)) dut(
 .clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(valid),.request_ready(ready),
 .request_write(write),.request_address(addr),.request_burst_data(payload),
 .response_valid(rsp_valid),.response_data(rsp_data),.idle(idle),.sdram_a(a),.sdram_bs(ba),
 .sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),
 .sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(ldqm),.sdram_udqm(udqm));
 sdram_model_burst model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(ldqm),.udqm(udqm),.dq(dq));
 integer i,j,k,base;reg[15:0] expected[0:9599];reg[15:0] value;
 initial begin
  for(i=0;i<9600;i=i+1)begin expected[i]=16'hdead;model.mem[i]=16'hbeef;end
  repeat(5)@(negedge clk);reset=0;
  for(i=0;i<1200;i=i+1)begin
   // A permutation visits every aligned burst once and jumps among rows.
   base=((i*17)%1200)*8;
   @(negedge clk);addr=base;valid=1;
   for(j=0;j<8;j=j+1)begin value=(base+j)^16'h5a96;payload[j*16+:16]=value;expected[base+j]=value;end
   while(!ready)@(negedge clk);
   @(negedge clk);valid=0;
  end
  while(!idle)@(negedge clk);
  repeat(5)@(negedge clk);
  if(model.writes!==9600 || model.write_bursts!==1200)$fatal(1,"write count %0d bursts %0d",model.writes,model.write_bursts);
  if(model.refreshes<10 || model.mrs!==1)$fatal(1,"refresh/mode counts %0d %0d",model.refreshes,model.mrs);
  for(k=0;k<9600;k=k+1)if(model.mem[k]!==expected[k])$fatal(1,"pixel mismatch at %0d got %h expected %h",k,model.mem[k],expected[k]);
  // Exercise the actual controller read path after mixed row/refresh traffic.
  write=0;
  for(i=0;i<40;i=i+1)begin
   base=((i*29)%1200)*8;
   @(negedge clk);addr=base;valid=1;while(!ready)@(negedge clk);
   @(negedge clk);valid=0;j=0;
   while(j<8)begin @(negedge clk);if(rsp_valid)begin
    if(rsp_data!==expected[base+j])$fatal(1,"read mismatch addr=%0d beat=%0d got=%h expected=%h",base,j,rsp_data,expected[base+j]);
    j=j+1;
   end end
  end
  while(!idle)@(negedge clk);
  $display("TEST_PASS_BURST writes=%0d bursts=%0d refreshes=%0d",model.writes,model.write_bursts,model.refreshes);$finish;
 end
 initial begin #10000000;$fatal(1,"watchdog");end
endmodule
