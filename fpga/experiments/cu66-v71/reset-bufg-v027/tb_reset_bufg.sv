`timescale 1ns/1ps
module tb_reset_bufg;
 reg clk=0;always #5 clk=~clk;
 reg platform_reset_ref=1;
 (* ASYNC_REG="TRUE" *)reg[3:0]old_sync=15,new_sync=15;
 always @(posedge clk or posedge platform_reset_ref)if(platform_reset_ref)old_sync<=15;else old_sync<={old_sync[2:0],1'b0};
 always @(posedge clk or posedge platform_reset_ref)if(platform_reset_ref)new_sync<=15;else new_sync<={new_sync[2:0],1'b0};
 wire rst;BUFG dut(.I(new_sync[3]),.O(rst));
 integer checks=0,assertions=0,releases=0;reg[31:0]seed=32'hac35d608;
 always @(posedge clk or negedge clk or posedge platform_reset_ref)begin #1;if(old_sync!==new_sync||rst!==old_sync[3])$fatal(1,"buffer changed reset logic/latency");checks=checks+1;end
 initial begin
  #13;platform_reset_ref=0;repeat(8)@(posedge clk);#1;if(rst!==0)$fatal(1,"release failure");
  for(integer i=0;i<100;i=i+1)begin
   seed={seed[30:0],seed[31]^seed[21]^seed[1]^seed[0]};#(1+seed%19);platform_reset_ref=1;assertions=assertions+1;#1;if(rst!==1)$fatal(1,"async assertion not preserved");#(1+seed%23);platform_reset_ref=0;
   repeat(5)@(posedge clk);#1;if(rst!==0)$fatal(1,"four-stage release not preserved");releases=releases+1;
  end
  $display("RESET_BUFG_UNISIM_PASS checks%0d async_assertions%0d releases%0d original_four_stages_preserved no_added_cycle",checks,assertions,releases);$finish;
 end
 initial begin #100000;$fatal(1,"watchdog");end
endmodule
