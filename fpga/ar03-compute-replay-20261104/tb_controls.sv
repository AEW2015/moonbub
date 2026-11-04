`timescale 1ns/1ps
module tb;
 reg clk=0;always #5 clk=!clk;
 reg reset=1,bw=0;reg[11:0]addr=0;reg[31:0]wd=0;wire[31:0]rd;
 ar03_fixture_diagnostic #(.WATCHDOG_CYCLES(64)) dut(.clk(clk),.reset(reset),.bus_write(bw),.bus_address(addr),.bus_wdata(wd),.bus_rdata(rd));
 integer checks=0;reg[31:0]v;
 task cmd(input[31:0]value);begin
  @(negedge clk);bw=1;addr=12'h408;wd=value;@(negedge clk);bw=0;
 end endtask
 task csr(input[11:0]address,input[31:0]value);begin
  @(negedge clk);addr=address;#1;if(rd!==value)$fatal(1,"CSR %h expected=%h got=%h",address,value,rd);checks=checks+1;
 end endtask
 initial begin
  repeat(4)@(negedge clk);reset=0;
  csr(12'h400,32'h31444b41);csr(12'h404,32'h00010000);csr(12'h4fc,0);
  cmd(3);csr(12'h440,1);csr(12'h40c,0);
  force dut.ks=0;cmd(1);repeat(70)@(negedge clk);
  csr(12'h41c,32'hf03);csr(12'h444,1);release dut.ks;
  cmd(4);csr(12'h40c,0);
  cmd(1);repeat(75)@(negedge clk);csr(12'h41c,32'hf02);csr(12'h444,2);
  // Inject downstream terminal events to test controller latching only.
  cmd(1);wait(dut.state==2);@(negedge clk);
  force dut.ev=1;force dut.es=8;force dut.ec=3;
  @(negedge clk);release dut.ev;release dut.es;release dut.ec;
  csr(12'h41c,32'h803);csr(12'h444,3);
  cmd(1);wait(dut.state==2);@(negedge clk);
  force dut.cv=1;force dut.co=0;force dut.ce=1;
  @(negedge clk);release dut.cv;release dut.co;release dut.ce;
  csr(12'h41c,32'hf01);csr(12'h444,4);
  cmd(2);repeat(3)@(negedge clk);csr(12'h40c,32'h46);
  cmd(4);csr(12'h40c,0);
  cmd(1);repeat(8)@(negedge clk);reset=1;repeat(3)@(negedge clk);reset=0;
  csr(12'h40c,0);csr(12'h420,0);csr(12'h440,0);csr(12'h444,0);
  $display("PASS controller checks=%0d admission_watchdog=1 execution_watchdog=1 injected_error=1 stale_completion=1 reset=1",checks);$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
