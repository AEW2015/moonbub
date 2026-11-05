`timescale 1ns/1ps
// Same source-bound core; reduced watchdog limit exercises timeout semantics
// without simulating 50,000,000 cycles. The production limit is not changed.
module tb_legacy_watchdog;
 reg clk=0;always #5 clk=!clk;
 reg reset=1,wr=0;reg[11:0]addr=0;reg[31:0]data=0;wire[31:0]rd;
 wire front,valid,pattern,pv;wire[23:0]pa;wire[15:0]rgb;integer unexpected=0;
 moonshine_core #(.WATCHDOG_CYCLES(64)) dut(.clk(clk),.reset(reset),
  .bus_write(wr),.bus_address(addr),.bus_wdata(data),.bus_rdata(rd),
  .frame_boundary(1'b1),.memory_idle(1'b1),.front_buffer(front),.front_valid(valid),.pattern_enable(pattern),
  .pixel_valid(pv),.pixel_ready(1'b1),.pixel_address(pa),.pixel_rgb565(rgb),.scanout_underruns(32'd0),.transport_overflows(32'd0));
 task write_reg(input[11:0]a,input[31:0]d);begin @(negedge clk);addr=a;data=d;wr=1;@(negedge clk);wr=0;end endtask
 task check_reg(input[11:0]a,input[31:0]v);begin @(negedge clk);addr=a;#1;if(rd!==v)$fatal(1,"reg %x actual %x expected %x",a,rd,v);end endtask
 always @(posedge clk)if(pv)unexpected<=unexpected+1;
 initial begin
  repeat(8)@(negedge clk);reset=0;@(negedge clk);
  // Seed a completed front-frame ownership state. End-to-end test separately
  // establishes a real JPEG frame, rather than relying on this shortcut.
  dut.front_buffer=1;dut.front_valid=1;dut.pattern_enable=0;dut.last_presented=77;dut.presented_frames=1;
  write_reg('h14,78);write_reg('h18,4);write_reg('h1c,{16'd720,16'd480});write_reg('h20,32'h10f02a67);write_reg('h24,1);
  write_reg('h100,'hff);write_reg('h100,'hd8);write_reg('h100,'hff);write_reg('h100,'hd9);write_reg('h24,4);
  check_reg('h2c,1);repeat(100)@(negedge clk);check_reg('h38,1);check_reg('h3c,1);
  if(!front||!valid||pattern||dut.last_presented!=77||dut.presented_frames!=1||unexpected!=0)$fatal(1,"watchdog altered front frame");
  write_reg('h24,2);check_reg('h10,1);
  $display("LEGACY_WATCHDOG_PASS timeout_override_cycles=64 preserved=1 abort_ready=1");$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
