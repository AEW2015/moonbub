`timescale 1ns/1ps
module tb_tagged_gateway;
 reg clk=0;always #5 clk=~clk;
 reg reset=1;reg[31:0] epoch_in=17;
 reg req_valid=0,ack_ready=0;wire req_ready,ack_valid;
 reg[31:0] req_seq=0,req_epoch=17,req_generation=0,req_frame_id=0,req_crc=0;
 reg[1:0] req_op=0;reg req_bank=0;reg[15:0] req_length=0,req_offset=0;reg[7:0] req_data=0;
 wire[31:0] ack_seq,ack_epoch,ack_generation;wire[3:0] ack_status,ack_detail;
 wire ack_bank;wire[15:0] ack_count;wire mem_we,mem_bank;wire[15:0] mem_addr;wire[7:0] mem_data;
 reg decode_request=0,decode_done=0,decode_fail=0,vblank=0;
 wire decode_grant,decode_bank,present,front_valid;wire[31:0] decode_id,front_id,accepted_frames,dropped_frames;
 tagged_gateway dut(.*);
 integer writes=0,acks=0,cycles=0;
 always @(posedge clk) begin cycles<=cycles+1;if(!reset && mem_we)writes<=writes+1;end
 task automatic body(input[31:0] s,input[1:0] op,input[31:0] epoch,input bit bank,input[31:0] gen,
                     input[31:0] id,input[15:0] len,input[31:0] crc,input[15:0] ofs,input[7:0] data);
 begin req_seq=s;req_op=op;req_epoch=epoch;req_bank=bank;req_generation=gen;req_frame_id=id;
  req_length=len;req_crc=crc;req_offset=ofs;req_data=data;end endtask
 task automatic transaction(input[3:0] status,input[15:0] count,input integer stall);
 reg[120:0] saved;integer n;
 begin
  @(negedge clk);req_valid=1;
  n=0;while(!req_ready)begin @(negedge clk);n=n+1;if(n>20)$fatal(1,"request timeout");end
  @(negedge clk);req_valid=0;
  n=0;while(!ack_valid)begin @(negedge clk);n=n+1;if(n>20)$fatal(1,"ack timeout");end
  if(ack_seq!==req_seq || ack_status!==status || ack_count!==count || ack_epoch!==epoch_in)
   $fatal(1,"bad ack seq=%0d status=%0d detail=%0d count=%0d",ack_seq,ack_status,ack_detail,ack_count);
  saved={ack_seq,ack_status,ack_detail,ack_epoch,ack_bank,ack_generation,ack_count};
  repeat(stall)begin @(negedge clk);if(!ack_valid || req_ready || saved!=={ack_seq,ack_status,ack_detail,ack_epoch,ack_bank,ack_generation,ack_count})$fatal(1,"unstable held ack");end
  acks=acks+1;ack_ready=1;@(negedge clk);ack_ready=0;
 end endtask
 reg b0,b1;reg[31:0] g0,g1,g2;integer before_writes;
 initial begin
  repeat(3)@(negedge clk);reset=0;
  // First accepted begin and exact replay after a lost acknowledgement.
  body(1,0,17,0,0,100,3,32'h352441c2,0,0);transaction(0,0,3);b0=ack_bank;g0=ack_generation;
  if(g0==0)$fatal(1,"zero initial generation");
  transaction(0,0,0);if(ack_bank!==b0||ack_generation!==g0||!dut.control.receiving)$fatal(1,"begin replay reapplied");
  req_frame_id=101;transaction(2,0,0);req_frame_id=100;
  // Exactly one memory write even when a successful DATA ACK is lost/retried.
  body(2,1,17,b0,g0,0,0,0,0,"a");transaction(0,1,4);before_writes=writes;
  transaction(0,1,0);if(writes!=before_writes||writes!=1)$fatal(1,"duplicate wrote twice");
  body(3,1,17,b0,g0,0,0,0,2,"b");transaction(5,1,0);if(writes!=1)$fatal(1,"bad offset wrote");
  body(4,1,17,b0,g0,0,0,0,1,"b");transaction(0,2,0);
  body(5,1,17,b0,g0,0,0,0,2,"c");transaction(0,3,0);
  body(6,2,17,b0,g0,0,0,0,0,0);transaction(0,3,0);
  transaction(0,3,0); // exact COMMIT replay after ACK loss: no second commit
  if(accepted_frames!=1||writes!=3)$fatal(1,"first commit");
  // Receive/abort a second bank, then allocate the same bank with new token.
  body(7,0,17,0,0,101,3,32'h352441c2,0,0);transaction(0,0,0);b1=ack_bank;g1=ack_generation;
  if(b1==b0||g1==g0)$fatal(1,"wrong second allocation");
  body(8,3,17,b1,g1,0,0,0,0,0);transaction(0,0,0);transaction(0,0,0);
  body(9,0,17,0,0,102,3,32'h352441c2,0,0);transaction(0,0,0);g2=ack_generation;
  if(ack_bank!=b1||g2==g1)$fatal(1,"generation did not advance on reuse");
  body(10,1,17,b1,g1,0,0,0,0,"x");transaction(4,0,0);if(writes!=3)$fatal(1,"stale data wrote");
  body(11,3,17,b1,g1,0,0,0,0,0);transaction(4,0,0);if(!dut.control.receiving)$fatal(1,"stale abort killed new frame");
  body(12,1,17,b1,g2,0,0,0,0,"a");transaction(0,1,0);
  body(13,1,17,b1,g2,0,0,0,1,"b");transaction(0,2,0);
  body(14,1,17,b1,g2,0,0,0,2,"c");transaction(0,3,0);
  body(15,2,17,b1,g2,0,0,0,0,0);transaction(0,3,0);
  if(accepted_frames!=2||writes!=6)$fatal(1,"second commit");
  // Old ACK is outside the one-entry replay window; out-of-order is not executed.
  body(14,1,17,b1,g2,0,0,0,2,"c");transaction(1,0,0);if(writes!=6)$fatal(1,"old sequence wrote");
  body(16,0,17,0,0,103,3,32'h352441c2,0,0);transaction(6,0,0);
  if(ack_detail!=2)$fatal(1,"busy detail");
  // Presentation order preserved; requests from an old reset epoch rejected.
  @(negedge clk);decode_request=1;@(negedge clk);decode_request=0;
  if(!decode_grant||decode_id!=100)$fatal(1,"oldest frame grant");
  @(negedge clk);decode_done=1;@(negedge clk);decode_done=0;vblank=1;@(negedge clk);vblank=0;
  if(!front_valid||front_id!=100)$fatal(1,"first frame lost");
  @(negedge clk);reset=1;epoch_in=18;@(negedge clk);reset=0;
  body(1,0,17,0,0,1,3,32'h352441c2,0,0);transaction(3,0,0);
  body(2,0,18,0,0,1,3,32'h352441c2,0,0);transaction(0,0,0);
  if(ack_epoch!=18)$fatal(1,"epoch reset failed");
  b1=ack_bank;g1=ack_generation;
  body(3,1,18,b1,g1,0,0,0,0,"x");transaction(0,1,0);
  body(4,1,18,b1,g1,0,0,0,1,"y");transaction(0,2,0);
  body(5,1,18,b1,g1,0,0,0,2,"z");transaction(0,3,0);
  body(6,2,18,b1,g1,0,0,0,0,0);transaction(6,3,0);if(ack_detail!=3)$fatal(1,"CRC detail");
  transaction(6,3,0); // negative responses are also replayed without effects
  body(7,1,18,b1,g1,0,0,0,0,"a");transaction(4,0,0);if(dut.active)$fatal(1,"CRC failure remained active");
  // Directly seed counters at their limits to exercise fail-closed wrap paths;
  // this is testbench instrumentation, not a 2^32-request endurance test.
  @(negedge clk);reset=1;epoch_in=19;@(negedge clk);reset=0;dut.generation=32'hffffffff;
  body(1,0,19,0,0,1,3,32'h352441c2,0,0);transaction(7,0,0);
  @(negedge clk);reset=1;epoch_in=20;@(negedge clk);reset=0;dut.next_seq=32'hffffffff;
  body(32'hffffffff,0,20,0,0,1,3,32'h352441c2,0,0);transaction(0,0,0);
  transaction(0,0,0); // latest acknowledged request is still replayable
  body(0,3,20,ack_bank,ack_generation,0,0,0,0,0);transaction(1,0,0);
  // Reset while a BEGIN ACK is deliberately held: ACK and active ownership
  // must be revoked and a never-reused epoch rejects its old token.
  @(negedge clk);reset=1;epoch_in=21;@(negedge clk);reset=0;
  body(1,0,21,0,0,1,3,32'h352441c2,0,0);
  @(negedge clk);if(!req_ready)$fatal(1,"reset request not ready");req_valid=1;
  @(negedge clk);req_valid=0;
  while(!ack_valid)@(negedge clk);
  if(ack_status!=0||!dut.active)$fatal(1,"missing held BEGIN ACK");b1=ack_bank;g1=ack_generation;
  @(negedge clk);reset=1;epoch_in=22;@(posedge clk);#1;
  if(ack_valid||dut.active||dut.control.receiving||dut.cache_valid)$fatal(1,"reset retained ACK or owner");
  @(negedge clk);reset=0;
  body(1,1,21,b1,g1,0,0,0,0,"a");transaction(3,0,0);
  body(2,0,22,0,0,2,3,32'h352441c2,0,0);transaction(0,0,0);b0=ack_bank;g0=ack_generation;
  body(3,3,21,b1,g1,0,0,0,0,0);transaction(3,0,0);if(!dut.active)$fatal(1,"old epoch abort changed owner");
  body(4,1,22,b0,g0,0,0,0,0,"a");transaction(0,1,0);
  $display("TEST_PASS_TAGGED_GATEWAY acks=%0d writes=%0d cycles=%0d",acks,writes,cycles);$finish;
 end
 initial begin #1000000;$fatal(1,"watchdog");end
endmodule
