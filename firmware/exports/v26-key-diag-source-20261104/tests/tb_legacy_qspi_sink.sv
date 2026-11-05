`timescale 1ns/1ps
// Use the exact core source bound to build-marker-fix-v2 and the bound vendor
// JPEG RTL. The QSPI bridge has its own pin-level tests; this test proves the
// legacy core's count/CRC gate and preservation/recovery behavior.
module tb_legacy_qspi_sink;
 reg clk=0;always #5 clk=!clk;
 reg reset=1,wr=0;reg[11:0]addr=0;reg[31:0]data=0;wire[31:0]rd;
 reg boundary=0;wire front,valid,pattern,pv;wire[23:0]pa;wire[15:0]rgb;
 integer fd,n,i,pixels=0,cycles=0;reg[7:0]jpeg[0:262143];reg[31:0]fixture_crc=32'hffffffff;
 reg watch_writes=0;integer unexpected_pixels=0;
 moonshine_core #(.WATCHDOG_CYCLES(4000000)) dut(.clk(clk),.reset(reset),
  .bus_write(wr),.bus_address(addr),.bus_wdata(data),.bus_rdata(rd),
  .frame_boundary(boundary),.memory_idle(1'b1),.front_buffer(front),.front_valid(valid),.pattern_enable(pattern),
  .pixel_valid(pv),.pixel_ready(1'b1),.pixel_address(pa),.pixel_rgb565(rgb),.scanout_underruns(32'd0),.transport_overflows(32'd0));
 task write_reg(input[11:0]a,input[31:0]d);begin @(negedge clk);addr=a;data=d;wr=1;@(negedge clk);wr=0;end endtask
 task check_reg(input[11:0]a,input[31:0]v);begin @(negedge clk);addr=a;#1;if(rd!==v)$fatal(1,"reg %x actual %x expected %x",a,rd,v);end endtask
 task configure(input[31:0]bytes,input[31:0]crc,input[31:0]id);begin
  write_reg('h14,id);write_reg('h18,bytes);write_reg('h1c,{16'd720,16'd480});write_reg('h20,crc);write_reg('h24,1);
 end endtask
 task send_fixture(input[31:0]id);begin
  configure(n,fixture_crc,id);for(i=0;i<n;i=i+1)write_reg('h100,jpeg[i]);write_reg('h24,4);
  while(!dut.pending && cycles<5000000)@(negedge clk);
  if(!dut.pending)$fatal(1,"JPEG decode failed: faults=%0d",dut.faults);
  boundary=1;@(negedge clk);boundary=0;@(negedge clk);
 end endtask
 task preserved;begin
  if(!valid||!front||pattern||dut.last_presented!=1||dut.presented_frames!=1)
   $fatal(1,"legacy test disturbed front frame");
  if(unexpected_pixels!=0)$fatal(1,"synthetic stream emitted %0d pixels",unexpected_pixels);
 end endtask
 always @(posedge clk)begin cycles<=cycles+1;if(pv)begin pixels<=pixels+1;if(watch_writes)unexpected_pixels<=unexpected_pixels+1;end end
 initial begin
  fd=$fopen("host/fixtures/pattern-720x480-420-q65.jpg","rb");if(fd==0)$fatal(1,"fixture missing");
  n=$fread(jpeg,fd);$fclose(fd);for(i=0;i<n;i=i+1)fixture_crc=dut.crc_byte(fixture_crc,jpeg[i]);fixture_crc=~fixture_crc;
  repeat(8)@(negedge clk);reset=0;
  // Decode one actual JPEG to establish a real presented front buffer.
  send_fixture(1);if(!valid||!front||pattern||pixels!=345600)$fatal(1,"baseline frame failed");
  check_reg('h34,1);watch_writes=1;
  // Full-size 256 KiB FFD8 + zeros + FFD9, independent IEEE CRC32 d499b869.
  configure(262144,32'hd499b869,2);
  for(i=0;i<262144;i=i+1)write_reg('h100, i==0 ? 8'hff : i==1 ? 8'hd8 : i==262142 ? 8'hff : i==262143 ? 8'hd9 : 8'h00);
  check_reg('h28,262144);write_reg('h24,4);check_reg('h2c,2);
  // Model a delayed host abort: malformed entropy-free data may run, but must
  // never emit pixels or change frame ownership. Actual 40 MHz QSPI latency
  // is not modeled here and must be bounded by separate pin-level checks.
  repeat(10000)@(negedge clk);preserved();write_reg('h24,2);check_reg('h10,1);preserved();
  // Negative CRC must fail the gate despite an otherwise identical byte count.
  configure(4,32'h1,3);write_reg('h100,'hff);write_reg('h100,'hd8);write_reg('h100,'hff);write_reg('h100,'hd9);
  check_reg('h28,4);write_reg('h24,4);check_reg('h2c,2);check_reg('h38,1);write_reg('h24,2);preserved();
  // Truncated data also fails, without changing the last valid front frame.
  configure(4,32'h0,4);write_reg('h100,'hff);write_reg('h100,'hd8);write_reg('h24,4);
  check_reg('h2c,2);check_reg('h38,2);write_reg('h24,2);preserved();
  // A valid frame still decodes and presents after the synthetic transaction.
  watch_writes=0;send_fixture(5);if(!valid||front||pattern||dut.last_presented!=5||dut.presented_frames!=2)$fatal(1,"post-abort recovery failed");
  $display("LEGACY_SINK_PASS full_bytes=262144 crc=d499b869 negative_crc=1 truncated=1 preserved=1 abort_recovery=1");$finish;
 end
 initial begin #100000000;$fatal(1,"timeout");end
endmodule
