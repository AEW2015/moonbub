`timescale 1ns/1ps
module tb_moonbub_tile_transpose;
 reg clk=0,reset=1,abort=0,in_valid=0,out_ready=0;
 reg [23:0] in_address=0;reg[15:0] in_data=0;
 wire in_ready,out_valid,first,last,fault;wire[23:0] out_address;wire[15:0] out_data;
 integer received=0;reg [31:0] random_state=32'h4aa31427;reg force_stall=0;
 reg held=0;reg[41:0] held_value;
 always #5 clk=~clk;
 moonbub_tile_transpose dut(clk,reset,abort,in_valid,in_ready,in_address,in_data,
  out_valid,out_ready,out_address,out_data,first,last,fault);
 always @(negedge clk) begin
  random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
  out_ready<=force_stall ? 1'b0 : (random_state[0] | random_state[3]);
 end
 always @(posedge clk) begin
  if(reset || abort) held<=0;
  else begin
   if(held && (!out_valid || {out_address,out_data,first,last}!==held_value))
    $fatal(1,"output changed under backpressure");
   held<=out_valid && !out_ready;
   held_value<={out_address,out_data,first,last};
   if(out_valid && out_ready) begin
    if(out_address!==24'h090000+((received%64)/8)*480+(received%8))
     $fatal(1,"address mismatch at %0d",received);
    if(out_data!==((received%8)*8+((received%64)/8)+(received/64)*100))
     $fatal(1,"data mismatch at %0d",received);
    if(first!==((received%8)==0) || last!==((received%8)==7))
     $fatal(1,"burst qualifier mismatch");
    received<=received+1;
   end
  end
 end
 task automatic block(input integer n);
  integer i;
  begin
   for(i=0;i<64;i=i+1)begin
    @(negedge clk);while(!in_ready)@(negedge clk);
    in_valid=1;in_address=24'h090000+(i%8)*480+(i/8);in_data=i+n*100;
    @(negedge clk);in_valid=0;
   end
  end
 endtask
 initial begin
  repeat(4)@(negedge clk);reset=0;
  block(0);block(1);
  wait(received==128);@(negedge clk);
  // Abort a complete buffered block while output is backpressured.
  force_stall=1;repeat(2)@(negedge clk);block(2);wait(out_valid);
  repeat(4)@(negedge clk);if(!out_valid || out_ready)$fatal(1,"expected stalled output");
  abort=1;@(negedge clk);abort=0;force_stall=0;@(negedge clk);
  if(out_valid || fault || received!=128)$fatal(1,"abort during output failed");
  // A partial block must be discarded without producing an output.
  in_valid=1;in_address=24'h090000;in_data=17;@(negedge clk);in_valid=0;
  abort=1;@(negedge clk);abort=0;
  repeat(5)@(negedge clk);if(out_valid || fault)$fatal(1,"abort failed");
  // Misaligned first address must fault and suppress the entire block.
  in_valid=1;in_address=24'h090001;@(negedge clk);in_valid=0;
  repeat(2)@(negedge clk);if(!fault || out_valid || in_ready)$fatal(1,"invalid block accepted");
  abort=1;@(negedge clk);abort=0;@(negedge clk);
  if(fault || !in_ready)$fatal(1,"fault not cleared");
  $display("TEST_PASS blocks=2 pixels=128 backpressure abort_input abort_output invalid_address");$finish;
 end
 initial begin #500000;$fatal(1,"watchdog timeout");end
endmodule
