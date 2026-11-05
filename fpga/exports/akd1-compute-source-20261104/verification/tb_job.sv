`timescale 1ns/1ps
module tb_job_qspi;
`include "top-harness.svh"
 integer core_edges=0,accepted_start=-1,observed_elapsed=-1,polls=0;reg[31:0]state_word,own,seq;
 always @(posedge dut.clk100)begin
  core_edges=core_edges+1;
  if(dut.rst100[3])begin accepted_start=-1;observed_elapsed=-1;end
  else begin
   if(dut.diagnostic.state==1&&dut.diagnostic.ks&&!dut.diagnostic.abort_command)accepted_start=core_edges;
   if(dut.diagnostic.state==2&&dut.diagnostic.cv&&!dut.diagnostic.abort_command)observed_elapsed=core_edges-accepted_start;
   if(dut.diagnostic.state==2&&dut.diagnostic.elapsed!=0&&dut.diagnostic.elapsed%500000==0)begin
    $display("REAL_QSPI_JOB_PROGRESS elapsed=%0d samples=%0d bytes=%0d",dut.diagnostic.elapsed,dut.diagnostic.samples,dut.diagnostic.bytes_sent);$fflush();
   end
  end
 end
 task idle_after_service_reset;
 begin force dut.locked=0;#100;release dut.locked;wait(!dut.rst100[3]&&!dut.rst200[3]);
  // Retained endpoint requires CS-high warmup after reset before selection.
  #200;
  check('h40c,-1,0);check('h420,-1,0);check('h424,-1,0);check('h444,-1,0);
 end endtask
 task cancel_queued_start_by_reset;
 begin
  force dut.clk100=0;write_reg('h408,1);read_reg('h40c,state_word);
  if(dut.bridge.wp==dut.bridge.rp)$fatal(1,"queued START setup did not enter bridge FIFO");
  force dut.locked=0;#100;release dut.clk100;#100;release dut.locked;
  wait(!dut.rst100[3]&&!dut.rst200[3]);
  #200;
  check('h40c,-1,0);check('h420,-1,0);check('h444,-1,0);
 end endtask
 initial begin
`ifdef AKD1_PLATFORM_STUB
  $fatal(1,"real job cannot use a stub");
`endif
  wait(!dut.rst100[3]&&!dut.rst200[3]&&!dut.rstpixel[3]);
  check('h000,-1,32'h31444b41);check('h004,-1,32'h00010000);check('h008,-1,0);check('h184,-1,32'h4d424b31);check('h400,-1,32'h31444b41);check('h404,-1,32'h00010000);
  cancel_queued_start_by_reset();
  // Boundary initialization is test-only, never a host/integration API. Check
  // opaque owner high bits without requiring billions of prior lab jobs.
  @(negedge dut.clk100);dut.diagnostic.next_owner=64'ha5f0123401020304;
  write_reg('h408,1);check('h40c,8,8);check('h420,-1,32'h01020304);check('h424,-1,32'ha5f01234);
  write_reg('h408,1);check('h440,-1,1);write_reg('h408,3);check('h440,-1,2);
  // Reset the actual active decoder, then verify fresh ownership/no replay.
  idle_after_service_reset();
  write_reg('h408,1);check('h40c,8,8);write_reg('h408,2);
  check('h40c,-1,32'h46);check('h420,-1,1);check('h444,-1,0);check('h430,-1,0);
  write_reg('h408,4);check('h40c,-1,0);check('h420,-1,1);
  write_reg('h408,1);check('h420,-1,2);
  state_word=0;polls=0;
  while(!state_word[4]&&!state_word[5]&&polls<1100)begin
   repeat(10000)@(negedge dut.clk100);read_reg('h40c,state_word);polls=polls+1;
  end
  if(state_word!==32'h13||observed_elapsed<=0)$fatal(1,"real job failed/timeout status%h polls%0d",state_word,polls);
  read_reg('h420,own);read_reg('h444,seq);if(own!==2||seq!==1)$fatal(1,"terminal snapshot identity");
  check('h410,-1,observed_elapsed);check('h414,-1,518400);check('h418,-1,48203);check('h41c,-1,0);
  check('h424,-1,0);check('h428,-1,1);check('h42c,-1,0);
  check('h430,-1,32'hee7dc9c6);check('h434,-1,32'h10bef275);check('h438,-1,32'h19ffddad);check('h43c,-1,32'h855898f0);
  check('h40c,-1,32'h13);check('h420,-1,own);check('h444,-1,seq);
  // STOP after completion may retain its incremented result sequence.
  write_reg('h408,2);check('h40c,-1,32'h46);check('h420,-1,2);check('h444,-1,1);check('h430,-1,0);
  write_reg('h408,4);check('h40c,-1,0);check('h444,-1,1);
  $display("AKD1_REAL_QSPI_JOB_PASS owner=2 samples=518400 bytes=48203 tag=855898f019ffddad10bef275ee7dc9c6 elapsed=%0d measured_posedges=1 queued_START_reset=1 reset_active_job=1 abort_before_after_completion=1 busy_reject=1 snapshot_guard=1 stub=0",observed_elapsed);$finish;
 end
 initial begin #150000000;$fatal(1,"real QSPI job timeout");end
endmodule
