`timescale 1ns/1ps
module tb_sdram_jpeg_writer;
 localparam integer BASE='h060000,MAX_BURSTS=16384;
 reg clk=0,reset=1,begin_valid=0,byte_valid=0,abort=0,sink_fault=0,force_stall=0;always #5 clk=~clk;
 reg[31:0]declared_length=0;reg[7:0]byte_data=0;
 wire begin_ready,begin_accept,begin_reject,byte_ready,write_valid,active,done,aborted,failed,faulted;
 wire[23:0]write_address;wire[127:0]write_data;wire[31:0]accepted_bytes,issued_bursts;
 integer cycle=0,busy=0,req_count=0;reg[127:0] memory[0:MAX_BURSTS-1];
 wire write_ready=!force_stall&&(busy==0)&&(cycle%5!=0);wire write_drain_done=(busy==0);
 sdram_jpeg_writer dut(.*);
 function automatic [7:0] value(input integer idx);value=8'(idx*13+49);endfunction
 integer index;reg held=0;reg[151:0]held_data;
 always @(posedge clk)begin
  cycle<=cycle+1;
  if(reset)begin busy<=0;req_count=0;held<=0;end
  else begin
   if(held && (!write_valid||held_data!=={write_address,write_data}))$fatal(1,"write changed under backpressure");
   held<=write_valid&&!write_ready;if(write_valid&&!write_ready)held_data<={write_address,write_data};
   if(busy>0)busy<=busy-1;
   if(write_valid&&write_ready)begin
    if(write_address[2:0]!=0 || {8'd0,write_address}!=BASE+req_count*8 || {8'd0,write_address}>=BASE+MAX_BURSTS*8)$fatal(1,"write address/order %h",write_address);
    index=({8'd0,write_address}-BASE)/8;memory[index]<=write_data;req_count=req_count+1;busy<=7;
   end
   if((done||aborted||failed)&&!write_drain_done)$fatal(1,"completion before drain");
   if(done&&(aborted||failed))$fatal(1,"conflicting completion");
  end
 end
 task automatic begin_frame(input integer n,input bit accept);
 begin
  @(negedge clk);declared_length=n;begin_valid=1;
  if(!begin_ready)$fatal(1,"begin not ready");
  @(negedge clk);begin_valid=0;
  if(begin_accept!==accept||begin_reject!==!accept)$fatal(1,"begin result n=%0d",n);
 end endtask
 task automatic put(input[7:0]b);
 integer wait_count;begin
  @(negedge clk);byte_data=b;byte_valid=1;wait_count=0;
  while(!byte_ready)begin @(negedge clk);wait_count=wait_count+1;if(wait_count>100)$fatal(1,"byte timeout");end
  @(negedge clk);byte_valid=0;
 end endtask
 task automatic run_length(input integer n);
 integer i,j,bursts,wait_count;reg[7:0]got;
 begin
  req_count=0;bursts=(n+15)/16;
  if(bursts<MAX_BURSTS)memory[bursts]=128'hfeedfacedeadbeeffeedfacedeadbeef;
  begin_frame(n,1);
  for(i=0;i<n;i=i+1)put(value(i));
  wait_count=0;while(!done)begin @(negedge clk);wait_count=wait_count+1;if(wait_count>1000)$fatal(1,"drain timeout");end
  if(active||faulted||accepted_bytes!=n||issued_bursts!=bursts||req_count!=bursts)$fatal(1,"length accounting n=%0d accepted=%0d bursts=%0d",n,accepted_bytes,req_count);
  for(i=0;i<bursts;i=i+1)for(j=0;j<16;j=j+1)begin
   got=memory[i][j*8+:8];
   if(got!==((i*16+j<n)?value(i*16+j):8'h00))$fatal(1,"payload/padding mismatch n=%0d i=%0d j=%0d got=%h",n,i,j,got);
  end
  if(bursts<MAX_BURSTS && memory[bursts]!==128'hfeedfacedeadbeeffeedfacedeadbeef)$fatal(1,"end guard changed");
 end endtask
 integer lens[0:12];integer i,n;reg saw_abort=0,saw_done=0;
 initial begin
  lens[0]=1;lens[1]=2;lens[2]=3;lens[3]=4;lens[4]=15;lens[5]=16;lens[6]=17;
  lens[7]=31;lens[8]=32;lens[9]=33;lens[10]=257;lens[11]=26991;lens[12]=262144;
  repeat(3)@(negedge clk);reset=0;
  begin_frame(0,0);begin_frame(262145,0);
  for(i=0;i<13;i=i+1)run_length(lens[i]);
  for(i=5;i<=14;i=i+1)run_length(i); // cover every possible last-burst remainder
  // Abort while an accepted burst is still waiting for the endpoint to drain.
  req_count=0;begin_frame(32,1);for(i=0;i<16;i=i+1)put(value(i));
  while(req_count==0)@(negedge clk);if(busy==0)$fatal(1,"abort setup did not overlap drain");
  abort=1;saw_abort=0;saw_done=0;
  while(!saw_abort)begin @(negedge clk);if(done)saw_done=1;if(aborted)saw_abort=1;end
  abort=0;if(saw_done||active||faulted||!write_drain_done)$fatal(1,"abort publication/drain failure");
  run_length(17);
  // Once offered and stalled, a request remains valid/data-stable even across
  // abort. It is handshaken exactly once, then drained without publishing.
  req_count=0;force_stall=1;begin_frame(16,1);for(i=0;i<16;i=i+1)put(value(i));
  while(!write_valid)@(negedge clk);repeat(2)@(negedge clk);
  abort=1;repeat(3)begin @(negedge clk);if(!write_valid)$fatal(1,"abort withdrew stalled offer");end
  force_stall=0;while(req_count==0)@(negedge clk);
  while(!aborted)@(negedge clk);
  if(req_count!=1||active||!write_drain_done)$fatal(1,"stalled abort drain failure");abort=0;
  // The same ready/valid rule applies to a fault while the offer is stalled.
  req_count=0;force_stall=1;begin_frame(16,1);for(i=0;i<16;i=i+1)put(value(i));
  while(!write_valid)@(negedge clk);repeat(2)@(negedge clk);
  sink_fault=1;repeat(3)begin @(negedge clk);if(!write_valid)$fatal(1,"fault withdrew stalled offer");end
  force_stall=0;while(req_count==0)@(negedge clk);
  while(!failed)@(negedge clk);
  if(req_count!=1||active||!faulted||!write_drain_done)$fatal(1,"stalled fault drain failure");
  sink_fault=0;@(negedge clk);reset=1;repeat(3)@(negedge clk);reset=0;
  // A sink fault is sticky, suppresses done, and is reported only after drain.
  req_count=0;begin_frame(32,1);for(i=0;i<16;i=i+1)put(value(i));
  while(req_count==0)@(negedge clk);if(busy==0)$fatal(1,"fault setup did not overlap drain");
  sink_fault=1;saw_done=0;while(!failed)begin @(negedge clk);if(done)saw_done=1;end
  if(saw_done||!faulted||active||!write_drain_done||begin_ready)$fatal(1,"sink fault handling");
  sink_fault=0;@(negedge clk);if(begin_ready)$fatal(1,"fault not sticky");
  $display("SDRAM_WRITER_PASS lengths=24 max_bytes=262144 tails=0..15 abort_drain=1 stalled_abort=1 stalled_fault=1 fault_drain=1");$finish;
 end
 initial begin #50000000;$fatal(1,"watchdog");end
endmodule
