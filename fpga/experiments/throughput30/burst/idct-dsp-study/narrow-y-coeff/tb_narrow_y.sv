`timescale 1ns/1ps
module tb_narrow_y;
 reg clk=0,rst=1,start=0,stop=0,valid=0; always #5 clk=~clk;
 reg [31:0] a=0,b=0,c=0,d=0;reg [2:0] idx=0;
 wire v0,v1;wire [31:0] o0,o1;wire [5:0] i0,i1;
 jpeg_idct_y ref_core(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(stop),.inport_valid_i(valid),.inport_data0_i(a),.inport_data1_i(b),.inport_data2_i(c),.inport_data3_i(d),.inport_idx_i(idx),.outport_valid_o(v0),.outport_data_o(o0),.outport_idx_o(i0));
 jpeg_idct_y_coeff test_core(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(stop),.inport_valid_i(valid),.inport_data0_i(a),.inport_data1_i(b),.inport_data2_i(c),.inport_data3_i(d),.inport_idx_i(idx),.outport_valid_o(v1),.outport_data_o(o1),.outport_idx_o(i1));
 reg [31:0] rng=32'h49ab7651; integer n;
 function automatic [31:0] next_rng(input [31:0] x); reg[31:0] y; begin y=x^(x<<13);y=y^(y>>17);next_rng=y^(y<<5);end endfunction
 initial begin
  repeat(5)@(negedge clk);rst=0;
  for(n=0;n<100000;n=n+1)begin
   @(negedge clk);rng=next_rng(rng);a=rng;rng=next_rng(rng);b=rng;rng=next_rng(rng);c=rng;rng=next_rng(rng);d=rng;rng=next_rng(rng);idx=rng[2:0];valid=rng[3];start=rng[8:4]==0;stop=rng[13:9]==0;rst=rng[21:14]==0;
   if(n%101==0)begin a=32'h80000000;b=32'h7fffffff;c=32'hffffffff;d=0;end
   @(posedge clk);#1;
   if(v0!==v1||o0!==o1||i0!==i1)$fatal(1,"NARROW_MISMATCH n=%0d idx=%0d v=%h/%h o=%h/%h i=%h/%h",n,idx,v0,v1,o0,o1,i0,i1);
  end
  $display("NARROW_Y_COEFF_EQ_PASS cycles=%0d seed=49ab7651",n);$finish;
 end
endmodule
