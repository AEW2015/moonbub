`timescale 1ns/1ps
module tb_admission;
 reg clk=0;always #5 clk=!clk;
 reg reset=1,abort=0,start_valid=0,in_valid=0,error_ready=0;
 reg [31:0] blocks=8192,owner=0,epoch=0,block_base=0;reg [15:0] width=256;
 wire start_ready,in_ready,out_valid,done_valid,error_valid,packet_validated;
 wire [31:0] out_owner,out_epoch;wire [3:0] error_code;
 integer cycles=0,accepted=0,started=0,valid_cases=0,rejections=0,abort_offsets=0,i;
 cp02_decoder dut(.clk(clk),.reset(reset),.abort(abort),.start_valid(start_valid),.start_ready(start_ready),
  .start_owner(owner),.start_epoch(epoch),.start_block_base(block_base),.start_bytes(32'd154),.start_blocks(blocks),.start_width(width),.start_plane(2'd0),
  .in_valid(in_valid),.in_ready(in_ready),.in_byte(8'h43),.in_last(1'b0),
  .out_valid(out_valid),.out_ready(1'b0),.out_owner(out_owner),.out_epoch(out_epoch),.packet_validated(packet_validated),
  .done_valid(done_valid),.done_ready(1'b0),.error_valid(error_valid),.error_ready(error_ready),.error_code(error_code));
 always @(posedge clk)begin
  cycles=cycles+1;if(cycles>10000)$fatal(1,"admission timeout");
  if(start_valid&&start_ready)begin accepted=0;started=cycles;end
  if(in_valid&&in_ready)accepted=accepted+1;
 end
 task launch(input [31:0] count,input [15:0] row_width,input integer tag);
 begin
  @(negedge clk);if(!start_ready)$fatal(1,"admission not idle");
  blocks=count;width=row_width;owner=tag;epoch=32'h60000000+tag;start_valid=1;in_valid=1;
  @(negedge clk);start_valid=0;
 end endtask
 task flush(input integer hard_reset);
 begin
  if(hard_reset)reset=1;else abort=1;
  #1;if(in_ready||start_ready||out_valid||done_valid||error_valid||packet_validated)$fatal(1,"admission cancellation mask");
  @(negedge clk);reset=0;abort=0;in_valid=0;
  repeat(3)@(negedge clk);
  if(!start_ready||out_epoch!==0||out_valid||done_valid||error_valid)$fatal(1,"admission stale ownership");
 end endtask
 task expect_ready;
 begin
  while(!in_ready&&!error_valid)@(negedge clk);
  if(error_valid||cycles-started!=15||accepted!=0)$fatal(1,"14-iteration admission failed elapsed%0d accepted%0d",cycles-started,accepted);
  if(out_owner!==owner||out_epoch!==epoch)$fatal(1,"admission identity");
  @(negedge clk);in_valid=0;
  if(accepted!=1)$fatal(1,"held first byte not accepted exactly once");valid_cases=valid_cases+1;
 end endtask
 task expect_reject(input integer latency);
 begin
  while(!error_valid)begin @(negedge clk);if(in_ready||accepted)$fatal(1,"invalid descriptor accepted bytes");end
  if(cycles-started!=latency)$fatal(1,"wrong admission rejection latency");
  repeat(9)begin
   if(error_code!==1||in_ready||start_ready||out_valid||done_valid||packet_validated||accepted||out_owner!==owner||out_epoch!==epoch)$fatal(1,"admission held error");
   @(negedge clk);
  end
  in_valid=0;error_ready=1;@(negedge clk);error_ready=0;rejections=rejections+1;
 end endtask
 initial begin
  repeat(3)@(negedge clk);reset=0;
  launch(8192,256,1);expect_ready();flush(0);
  launch(8192,1,2);expect_ready();flush(1);
  launch(256,256,3);expect_ready();flush(0);
  launch(8191,1,4);expect_ready();flush(1);
  launch(1,1,5);expect_ready();flush(0);
  launch(8192,255,6);expect_reject(15);
  launch(8191,256,7);expect_reject(15);
  launch(8193,256,8);expect_reject(1);
  launch(32'h10002000,256,9);expect_reject(1);
  launch(8192,16'h8100,10);expect_reject(1);
  launch(0,1,11);expect_reject(1);
  launch(1,0,12);expect_reject(1);
  block_base=32'hffffe000;launch(8192,256,13);expect_ready();flush(0);
  block_base=32'hffffe001;launch(8192,256,14);expect_reject(1);block_base=0;
  for(i=0;i<=15;i=i+1)begin
   launch(8192,256,100+i*2);repeat(i)@(negedge clk);
   if(accepted)$fatal(1,"first byte consumed before final admission cancellation");
   flush(i%2);abort_offsets=abort_offsets+1;
   launch(8192,256,101+i*2);expect_ready();flush(1-i%2);
  end
  $display("ADMISSION_PASS valid=%0d rejects=%0d abort_offsets=%0d held_first_byte=1 exact_remainder_steps=14 boundary_blocks=8192 boundary_width=256",valid_cases,rejections,abort_offsets);$finish;
 end
endmodule
