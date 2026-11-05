`timescale 1ns/1ps
module tb_ordering;
`include "top-harness.svh"
 integer n;reg[31:0]owner_expected=0;
 initial begin
  wait(!dut.rst100[3]&&!dut.rst200[3]&&!dut.rstpixel[3]);#200;
  // Every read uses exactly8 dummy bytes at16MHz, with no software delay.
  check('h400,-1,32'h31444b41);
  for(n=0;n<8;n=n+1)begin
   write_reg('h408,1);owner_expected=owner_expected+1;
   check('h40c,8,8);check('h420,-1,owner_expected);
   write_reg('h408,2);check('h40c,-1,32'h46);
   check('h444,-1,0);check('h430,-1,0);
   write_reg('h408,4);check('h40c,-1,0);
  end
  // Queue ordered START/STOP/CLEAR/unknown while core cannot consume. Read
  // immediately on resume: actual bridge empty/read-state barrier must drain.
  force dut.clk100=0;
  write_reg('h408,1);write_reg('h408,2);write_reg('h408,4);write_reg('h408,99);
  if(dut.bridge.wp==dut.bridge.rp)$fatal(1,"queued commands missing");
  release dut.clk100;
  owner_expected=owner_expected+1;
  check('h40c,-1,0);check('h420,-1,owner_expected);check('h440,-1,1);check('h444,-1,0);check('h430,-1,0);
  // A queued START followed by a read must observe the accepted command.
  force dut.clk100=0;write_reg('h408,1);release dut.clk100;
  owner_expected=owner_expected+1;
  check('h40c,8,8);check('h420,-1,owner_expected);
  write_reg('h408,2);check('h40c,-1,32'h46);write_reg('h408,4);check('h40c,-1,0);
  $display("AKD1_CSR_ORDERING_PASS checks=%0d minimum8dummybytes16MHz=1 immediate_START_STOP_CLEAR_reads=1 stoppedcore_queued_START_STOP_CLEAR_unknown=1 queue_drain_barrier=1 fullowner=1",checks);$finish;
 end
 initial begin #2000000;$fatal(1,"ordering timeout");end
endmodule
