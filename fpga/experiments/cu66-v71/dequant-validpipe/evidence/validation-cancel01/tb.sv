module tb_cancel;
logic clk=0;always #5 clk=~clk;
logic rst=1,abort_i=0,in_valid=0,in_ready,out_valid,out_ready=0,out_error;
logic[31:0]in_id=0,out_id;logic[1023:0]in_coefficients=0;
logic in_chroma=0;logic[1:0]in_scale_code=1;logic[1279:0]out_dequantized;
cu71_dequant_validpipe dut(.*);
task automatic tick;begin @(posedge clk);#1;end endtask
task automatic accept(input integer kind,input integer ident);
begin
 @(negedge clk);if(!in_ready)$fatal(1,"not ready");
 in_coefficients=0;in_chroma=1;in_scale_code=2;in_id=ident;
 if(kind==1)in_coefficients[15:0]=16'sd2048;
 if(kind==2)in_coefficients[15:0]=16'sd2049;
 if(kind==3)in_scale_code=3;
 in_valid=1;tick();if(dut.state!==2'd3||out_valid)$fatal(1,"new state missing");
 @(negedge clk);in_valid=0;
end endtask
initial begin
 repeat(3)tick();if(!$isunknown(out_dequantized)||!$isunknown(dut.bad_group))$fatal(1,"payload initialized");
 @(negedge clk);rst=0;
 for(integer kind=0;kind<2;kind=kind+1)begin
  accept(1,100+kind);if(kind==0)rst=1;else abort_i=1;
  tick();if(out_valid)$fatal(1,"cancelled validation leaked");
  @(negedge clk);rst=0;abort_i=0;#1;
  if(!in_ready||!$isunknown(out_dequantized))$fatal(1,"cancelled payload exposed");
 end
 for(integer kind=0;kind<4;kind=kind+1)begin
  accept(kind,200+kind);
  // Change coefficient range, zero status, chroma and scale after acceptance.
  in_coefficients=~in_coefficients;in_chroma=0;in_scale_code=0;
  for(integer wait_cycles=0;!out_valid;wait_cycles=wait_cycles+1)begin
   tick();if(wait_cycles>15)$fatal(1,"output timeout");
  end
  if(out_id!==32'(200+kind)||out_error!==1'(kind>=2))$fatal(1,"captured classification failed");
  if(kind==1)begin
   if(out_dequantized[19:0]!==20'd69632||out_dequantized[1279:20]!==0)$fatal(1,"captured quantizer/chroma failed");
  end else if(out_dequantized!==0)$fatal(1,"zero/error publication failed");
  repeat(3)begin tick();if(!out_valid||out_id!==32'(200+kind))$fatal(1,"stalled result changed");end
  @(negedge clk);out_ready=1;tick();@(negedge clk);out_ready=0;
 end
 $display("DEQUANT_VALIDATION_CANCEL_PASS direct_abort=1 direct_reset=1 poisoned_metadata_replays=4 unknown_payload_retained=1");$finish;
end
initial begin #10000;$fatal(1,"watchdog");end
endmodule
