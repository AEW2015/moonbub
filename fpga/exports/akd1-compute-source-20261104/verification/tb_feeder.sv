`timescale 1ns/1ps
module tb_feeder;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,bw=0,ready=0;reg[11:0]addr=0;reg[31:0]wd=0;wire[31:0]rd,pr;
 ar03_fixture_diagnostic dut(.clk(clk),.reset(reset),.bus_write(bw),.bus_address(addr),.bus_wdata(wd),.bus_rdata(rd));
 parent_fixture_diagnostic parent(.clk(clk),.reset(reset),.bus_write(bw),.bus_address(addr),.bus_wdata(wd),.bus_rdata(pr));
 integer checks=0,accepted=0,fetches=0,run,i;reg dofetch,masked_edge;reg[31:0]fetch_addr;reg[7:0]held_data;
 initial begin force dut.ki=ready;force parent.ki=ready;end
 always @(posedge clk)begin
  dofetch=dut.fixture_fetch_enable;masked_edge=reset||dut.cancel;fetch_addr=dut.bytes_sent;held_data=dut.byte_data;
  if((reset||dut.cancel)&&dofetch!==0)$fatal(1,"fetch active under reset/cancel");
  if(!reset&&dut.state==2&&dut.byte_valid&&ready&&!dut.abort_command)begin
   if(dut.byte_data!==parent.byte_data||dut.byte_data!==dut.rom[dut.bytes_sent])$fatal(1,"accepted byte mismatch index%0d",dut.bytes_sent);
   accepted=accepted+1;
  end
  #1;
  if(dut.byte_valid!==parent.byte_valid||dut.state!==parent.state||dut.bytes_sent!==parent.bytes_sent||dut.elapsed!==parent.elapsed||dut.samples!==parent.samples||dut.owner!==parent.owner||dut.result_sequence!==parent.result_sequence||rd!==pr)$fatal(1,"feeder observable/cycle mismatch");
  if(dut.byte_valid&&dut.byte_data!==parent.byte_data)$fatal(1,"valid payload mismatch");
  if(dofetch)begin if(dut.byte_data!==dut.rom[fetch_addr])$fatal(1,"synchronous fetch data/latency");fetches=fetches+1;end
  else if(dut.byte_data!==held_data)$fatal(1,"unreset data changed without fetch");
  if(masked_edge&&dut.byte_valid!==0)$fatal(1,"invalid mask missing");
  checks=checks+1;
 end
 task command(input[31:0]value);begin @(negedge clk);bw=1;addr='h408;wd=value;@(negedge clk);bw=0;end endtask
 initial begin
  repeat(6)@(negedge clk);reset=0;
  for(run=0;run<8;run=run+1)begin
   ready=0;command(1);wait(dut.state==2);repeat(20)@(negedge clk);
   if(!dut.byte_valid||dut.byte_data!==dut.rom[0]||dut.bytes_sent!==0)$fatal(1,"held first byte/first fetch timing");
   for(i=0;i<120;i=i+1)begin @(negedge clk);ready=((i+run)%7)!=3;end
   if(run%2==0)begin
    ready=run%4==0;command(2);repeat(4)@(negedge clk);
    if(dut.state!==6||dut.byte_valid!==0)$fatal(1,"cancel did not flush");
    command(4);
   end else begin
    reset=1;repeat(5)@(negedge clk);reset=0;repeat(4)@(negedge clk);
    if(dut.state!==0||dut.byte_valid!==0)$fatal(1,"reset did not flush");
   end
  end
  release dut.ki;release parent.ki;
  if(accepted<300||fetches<300)$fatal(1,"insufficient byte coverage");
  $display("GUARDED_ROM_FEEDER_EQUIVALENCE_PASS runs=8 checks=%0d accepted=%0d fetches=%0d held_first_byte=1 synchronous_latency=1 reset_cancel_no_fetch=1 unreset_data_holds=1 valid_masks_stale=1 parent_observables_cycle_equal=1",checks,accepted,fetches);$finish;
 end
 initial begin #100000;$fatal(1,"feeder timeout");end
endmodule
