module tb_validation_cancel;
logic clk=0;always #5 clk=~clk;
logic rst=1,abort_frame=0,in_valid=0,in_ready,out_valid,out_ready=0,out_error;
logic[31:0]in_id=0,out_id,active_cycles;
logic[1279:0]in_tile=0;logic[1535:0]out_tile;
cu71_idct_validpipe dut(.*);
task automatic tick;begin @(posedge clk);#1;end endtask
task automatic accept(input bit bad,input integer ident);
begin
 @(negedge clk);if(!in_ready)$fatal(1,"not input-ready");
 in_id=ident;in_tile=0;if(bad)in_tile[19:0]=20'h7ffff;in_valid=1;
 tick();if(dut.state!==4'd10||out_valid)$fatal(1,"validation stage not entered exclusively");
 @(negedge clk);in_valid=0;
end endtask
initial begin
 repeat(3)tick();if(!$isunknown(out_tile)||!$isunknown(dut.bad_group))$fatal(1,"payload unexpectedly initialized");
 @(negedge clk);rst=0;
 for(integer mode=0;mode<2;mode=mode+1)begin
  accept(0,100+mode);
  if(mode==0)abort_frame=1;else rst=1;
  tick();if(out_valid)$fatal(1,"cancelled validation leaked");
  @(negedge clk);abort_frame=0;rst=0;#1;
  if(!in_ready||!$isunknown(out_tile))$fatal(1,"cancelled validation published payload");
 end
 for(integer bad=0;bad<2;bad=bad+1)begin
  accept(1'(bad),200+bad);tick();
  if(!out_valid||out_id!==32'(200+bad)||out_error!==1'(bad)||out_tile!==1536'd0||active_cycles!==32'd1)
    $fatal(1,"validation replay/zero/error publication mismatch");
  repeat(4)begin tick();if(!out_valid||out_tile!==0||active_cycles!==1)$fatal(1,"stalled validation output changed");end
  @(negedge clk);out_ready=1;tick();@(negedge clk);out_ready=0;
 end
 $display("IDCT_VALIDATION_CANCEL_PASS abort_new_state=1 reset_new_state=1 unknown_payload_retained=1 zero_bad_replays=2 stalls=8");$finish;
end
initial begin #10000;$fatal(1,"watchdog");end
endmodule
