`timescale 1ns/1ps
module tb_two_bank;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,begin_valid=0,byte_valid=0,commit_valid=0,abort_valid=0,ingress_overflow=0;
 reg [31:0] begin_id=0,begin_crc=0;reg [15:0] begin_length=0;reg [7:0] byte_data=0;
 wire begin_accept,reject,mem_we,mem_bank,decode_grant,decode_bank,present,front_valid;wire[3:0] reject_reason;wire[15:0] mem_addr;wire[7:0] mem_data;wire[31:0] decode_id,front_id,accepted_frames,dropped_frames;
 reg decode_request=0,decode_done=0,decode_fail=0,vblank=0;
 reg[7:0] ram0[0:49151],ram1[0:49151];integer writes=0,idx;
 two_bank_control dut(.*);
 always @(posedge clk)if(mem_we)begin
  if(mem_addr>=49152)$fatal(1,"write outside cap");
  if(mem_bank)ram1[mem_addr]<=mem_data;else ram0[mem_addr]<=mem_data;
  writes<=writes+1;
 end
 always @(negedge clk)if(!reset)begin
  if(dut.receiving && dut.decoding && dut.recv_bank==dut.dec_bank)$fatal(1,"receive/decode share bank");
  if(dut.receiving && dut.pending && dut.recv_bank==dut.pending_bank)$fatal(1,"receive/pending share bank");
  if(dut.decoding && dut.pending)$fatal(1,"decoder overwrites pending framebuffer");
 end
 task begin_frame(input[31:0]id,input[15:0]len,input[31:0]crc,input bit accept,input[3:0]reason);
 begin @(negedge clk);begin_id=id;begin_length=len;begin_crc=crc;begin_valid=1;@(posedge clk);#1;
  if(begin_accept!==accept||reject!==!accept||(!accept&&reject_reason!==reason))$fatal(1,"begin mismatch id=%0d",id);
  @(negedge clk);begin_valid=0;
 end endtask
 task put(input[7:0]v);begin @(negedge clk);byte_data=v;byte_valid=1;@(posedge clk);#1;if(!mem_we||reject)$fatal(1,"byte rejected");@(negedge clk);byte_valid=0;end endtask
 task commit(input bit ok,input[3:0]reason);begin @(negedge clk);commit_valid=1;@(posedge clk);#1;if(reject!==!ok||(!ok&&reject_reason!==reason))$fatal(1,"CRC/length rejection mismatch");@(negedge clk);commit_valid=0;end endtask
 task grant(input bit ok,input[31:0]id);begin @(negedge clk);decode_request=1;@(posedge clk);#1;if(decode_grant!==ok||(ok&&decode_id!==id))$fatal(1,"decode grant mismatch expected=%0d",id);@(negedge clk);decode_request=0;end endtask
 task done;begin @(negedge clk);decode_done=1;@(posedge clk);#1;@(negedge clk);decode_done=0;end endtask
 task show(input bit ok,input[31:0]id);begin @(negedge clk);vblank=1;@(posedge clk);#1;if(present!==ok||(ok&&(!front_valid||front_id!==id)))$fatal(1,"presentation mismatch expected=%0d",id);@(negedge clk);vblank=0;end endtask
 task abc;begin put("a");put("b");put("c");end endtask
 task one_through_nine;begin put("1");put("2");put("3");put("4");put("5");put("6");put("7");put("8");put("9");end endtask
 initial begin
  repeat(3)@(negedge clk);reset=0;
  // 0x352441c2 is CRC-32/ISO-HDLC of "abc"; 0xcbf43926 of "123456789".
  begin_frame(10,3,32'h352441c2,1,0);abc();commit(1,0);grant(1,10);
  begin_frame(11,9,32'hcbf43926,1,0);begin_frame(12,3,32'h352441c2,0,2);
  one_through_nine();done();commit(1,0);
  if(ram0[0]!="a"||ram0[1]!="b"||ram0[2]!="c"||ram1[0]!="1"||ram1[8]!="9")$fatal(1,"banked write data mismatch");
  if(front_valid)$fatal(1,"front changed before vblank");grant(0,0);show(1,10);grant(1,11);done();
  if(front_id!=10)$fatal(1,"front changed before second vblank");show(1,11);
  // Oversize and zero length never allocate a bank or write memory.
  begin_frame(20,49153,0,0,1);begin_frame(20,0,0,0,1);
  // Exact 48 KiB is admissible; transport overflow discards partial receive.
  begin_frame(21,49152,0,1,0);put("a");
  @(negedge clk);ingress_overflow=1;@(posedge clk);#1;if(!reject||reject_reason!=5||mem_we)$fatal(1,"overflow handling");@(negedge clk);ingress_overflow=0;
  // Bad CRC, short commit, and data beyond announced length are rejected.
  begin_frame(22,3,32'h00000000,1,0);abc();commit(0,3);
  begin_frame(23,3,32'h352441c2,1,0);put("a");commit(0,4);
  begin_frame(24,1,32'he8b7be43,1,0);put("a");
  @(negedge clk);byte_data="b";byte_valid=1;@(posedge clk);#1;if(!reject||reject_reason!=5||mem_we)$fatal(1,"length overflow");@(negedge clk);byte_valid=0;
  // Conflicting final byte and COMMIT cannot produce a valid READY frame.
  begin_frame(25,3,32'h352441c2,1,0);put("a");
  @(negedge clk);byte_valid=1;commit_valid=1;@(posedge clk);#1;if(!reject||reject_reason!=6||mem_we)$fatal(1,"conflict");@(negedge clk);byte_valid=0;commit_valid=0;
  // Pending frame may be presented even when another receive is aborted on
  // the same clock; abort must never destroy that independent pending frame.
  begin_frame(30,3,32'h352441c2,1,0);abc();commit(1,0);grant(1,30);done();
  begin_frame(31,3,32'h352441c2,1,0);put("a");
  @(negedge clk);abort_valid=1;vblank=1;@(posedge clk);#1;
  if(!present||front_id!=30||!front_valid||mem_we)$fatal(1,"simultaneous abort/vblank lost pending frame");
  @(negedge clk);abort_valid=0;vblank=0;grant(0,0);
  // Two READY banks preserve commit order and block a third begin.
  begin_frame(40,3,32'h352441c2,1,0);abc();commit(1,0);
  begin_frame(41,3,32'h352441c2,1,0);abc();commit(1,0);
  begin_frame(42,3,32'h352441c2,0,2);grant(1,40);done();grant(0,0);show(1,40);grant(1,41);done();show(1,41);
  // Independent simultaneous decoder and receive failures must both count.
  begin_frame(50,3,32'h352441c2,1,0);abc();commit(1,0);grant(1,50);begin_frame(51,3,32'h352441c2,1,0);put("a");
  @(negedge clk);abort_valid=1;decode_fail=1;@(posedge clk);#1;if(front_id!=41||present)$fatal(1,"failure changed front");@(negedge clk);abort_valid=0;decode_fail=0;
  // Exercise every byte address through the exact 48 KiB limit; reference
  // CRC-32/ISO-HDLC of 49,152 zero bytes is 0x16d13407.
  begin_frame(60,49152,32'h16d13407,1,0);
  for(idx=0;idx<49152;idx=idx+1)put(0);
  commit(1,0);if(ram0[49151]!==0)$fatal(1,"last legal byte not written");
  grant(1,60);done();show(1,60);
  if(accepted_frames!=7 || dropped_frames!=8)$fatal(1,"counters accepted=%0d dropped=%0d",accepted_frames,dropped_frames);
  if(writes!=49185)$fatal(1,"write accounting %0d",writes);
  $display("TEST_PASS_TWO_BANK accepted=%0d dropped=%0d writes=%0d final_front=%0d",accepted_frames,dropped_frames,writes,front_id);$finish;
 end
 initial begin #5000000;$fatal(1,"watchdog");end
endmodule
