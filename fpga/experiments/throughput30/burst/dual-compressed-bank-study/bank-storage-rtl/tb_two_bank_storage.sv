`timescale 1ns/1ps
module tb_two_bank_storage;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,begin_valid=0,byte_valid=0,commit_valid=0,abort_valid=0,ingress_overflow=0;
 reg[31:0] begin_id=0,begin_crc=0;reg[15:0] begin_length=0;reg[7:0] byte_data=0;
 wire begin_accept,reject,decode_grant,decode_bank,present,front_valid,read_ready,read_valid,read_error;
 wire[3:0] reject_reason;wire[31:0] decode_id,front_id,accepted_frames,dropped_frames;wire[15:0] decode_length;wire[7:0] read_data;
 reg decode_request=0,decode_done=0,decode_fail=0,vblank=0,read_req=0;reg[15:0]read_addr=0;
 integer i,read_count=0,overlap_count=0;reg[7:0] before_reset_byte;
 two_bank_storage dut(.*);
 task begin_frame(input[31:0]id,input[15:0]len,input[31:0]crc,input bit ok,input[3:0]reason);
 begin @(negedge clk);begin_id=id;begin_length=len;begin_crc=crc;begin_valid=1;@(posedge clk);#1;
  if(begin_accept!==ok||reject!==!ok||(!ok&&reject_reason!==reason))$fatal(1,"begin mismatch id=%0d",id);
  @(negedge clk);begin_valid=0;
 end endtask
 task put(input[7:0]v);begin @(negedge clk);byte_data=v;byte_valid=1;@(posedge clk);#1;if(reject)$fatal(1,"byte rejected");@(negedge clk);byte_valid=0;end endtask
 task commit(input bit ok,input[3:0]reason);begin @(negedge clk);commit_valid=1;@(posedge clk);#1;if(reject!==!ok||(!ok&&reject_reason!==reason))$fatal(1,"commit check");@(negedge clk);commit_valid=0;end endtask
 task grant(input[31:0]id,input[15:0]length);begin @(negedge clk);decode_request=1;@(posedge clk);#1;
  if(!decode_grant||decode_id!=id||decode_length!=length)$fatal(1,"grant mismatch");
  if(read_ready)$fatal(1,"read ownership activated too early");
  @(negedge clk);decode_request=0;@(posedge clk);#1;if(!read_ready)$fatal(1,"read ownership not active");
 end endtask
 task read_byte(input[15:0]addr,input[7:0]expected);begin @(negedge clk);read_addr=addr;read_req=1;#1;
  if(read_valid||read_error)$fatal(1,"read responded before sampling edge");
  @(posedge clk);#1;if(!read_valid||read_error||read_data!==expected)$fatal(1,"read data mismatch addr=%0d got=%02x expected=%02x",addr,read_data,expected);read_count=read_count+1;
  @(negedge clk);read_req=0;@(posedge clk);#1;if(read_valid||read_error)$fatal(1,"read response did not clear");
 end endtask
 task invalid_read(input[15:0]addr);begin @(negedge clk);read_addr=addr;read_req=1;@(posedge clk);#1;
  if(read_valid||!read_error)$fatal(1,"read bound rejection addr=%0d",addr);@(negedge clk);read_req=0;@(posedge clk);#1;
 end endtask
 task done;begin @(negedge clk);decode_done=1;@(posedge clk);#1;if(read_ready)$fatal(1,"read remained active at done");@(negedge clk);decode_done=0;end endtask
 task show(input[31:0]id);begin @(negedge clk);vblank=1;@(posedge clk);#1;if(!present||!front_valid||front_id!=id)$fatal(1,"bad presentation");@(negedge clk);vblank=0;end endtask
 initial begin
  repeat(3)@(negedge clk);reset=0;
  // Deterministic fixture CRCs, calculated independently with Python zlib.
  begin_frame(0,1024,32'hb70b4c26,1,0);
  for(i=0;i<1024;i=i+1)put(i[7:0]);commit(1,0);grant(0,1024);
  // Simultaneously stream frame 1 into the other bank and read every byte of
  // decoder-owned frame 0. No shared source array is used as read data.
  begin_frame(1,1536,32'h93737851,1,0);
  for(i=0;i<1536;i=i+1)begin
   @(negedge clk);byte_valid=1;byte_data=8'(3*i+7);
   if(i<1024)begin read_req=1;read_addr=16'(i);end
   @(posedge clk);#1;
   if(reject)$fatal(1,"overlap byte rejected");
   if(i<1024)begin
    if(!read_valid||read_error||read_data!==8'(i))$fatal(1,"overlap read mismatch at %0d",i);
    read_count=read_count+1;overlap_count=overlap_count+1;
   end
   @(negedge clk);byte_valid=0;read_req=0;@(posedge clk);#1;
  end
  done();commit(1,0);invalid_read(0);show(0);grant(1,1536);
  for(i=0;i<1536;i=i+1)read_byte(16'(i),8'(3*i+7));
  invalid_read(1536);done();show(1);
  // CRC failure and receive abort do not grant decoder access to the bank.
  begin_frame(2,3,0,1,0);put("x");put("y");put("z");commit(0,3);invalid_read(0);
  begin_frame(3,3,32'heb8eba67,1,0);put("x");
  @(negedge clk);abort_valid=1;@(posedge clk);#1;@(negedge clk);abort_valid=0;invalid_read(0);
  // Reuse a previously longer bank. Only the new 3-byte logical frame may be read.
  begin_frame(4,3,32'h352441c2,1,0);put("a");put("b");put("c");commit(1,0);grant(4,3);
  read_byte(0,"a");read_byte(1,"b");read_byte(2,"c");invalid_read(3);
  // Reset while owning a bank must invalidate the read interface, regardless
  // of RAM contents; an idle read after reset is rejected.
  @(negedge clk);reset=1;read_req=1;read_addr=0;@(posedge clk);#1;
  if(read_ready||read_valid||read_error||front_valid)$fatal(1,"reset did not revoke access");
  @(negedge clk);reset=0;read_req=0;invalid_read(0);
  // Reset while receive write strobe is pending: the wrapper gates the RAM
  // write on reset and must revoke receive ownership without changing data.
  before_reset_byte=dut.compressed0[0];begin_frame(5,3,32'h352441c2,1,0);
  @(negedge clk);byte_valid=1;byte_data="x";@(posedge clk);#1;if(!dut.mem_we)$fatal(1,"expected pending write");
  @(negedge clk);byte_valid=0;reset=1;@(posedge clk);#1;
  if(dut.compressed0[0]!==before_reset_byte||dut.control.receiving||read_ready||read_valid)$fatal(1,"reset allowed pending write");
  @(negedge clk);reset=0;
  // Full 48 KiB frame: test every byte on the synchronous port, not just the
  // last byte. CRC-32 of 49,152 zeros = 0x16d13407.
  begin_frame(60,49153,0,0,1);begin_frame(60,49152,32'h16d13407,1,0);
  for(i=0;i<49152;i=i+1)put(0);commit(1,0);grant(60,49152);
  for(i=0;i<49152;i=i+1)read_byte(16'(i),0);invalid_read(49152);done();show(60);
  if(accepted_frames!=1||dropped_frames!=0)$fatal(1,"post-reset counters");
  if(read_count!=51715||overlap_count!=1024)$fatal(1,"read count %0d overlap %0d",read_count,overlap_count);
  $display("TEST_PASS_BANK_STORAGE reads=%0d overlap=%0d cap=49152 final_front=%0d",read_count,overlap_count,front_id);$finish;
 end
 initial begin #10000000;$fatal(1,"watchdog");end
endmodule
