`timescale 1ns/1ps
module tb_scale_unit;
 reg clk=0;always #5 clk=~clk;
 reg a_write=0,b_write=0,b_read=0;
 reg [10:0] a_addr=0,b_addr=0;reg [1:0] a_data=0,b_data=0;
 wire [1:0] b_q;
 cu66_scale_tdp_v107 dut(.*);
 reg [1:0] expected[0:1349];reg [1:0] held;reg known=0;
 integer clocks=0,collisions=0,dual_writes=0,priority_writes=0,holds=0;
 task step(input bit aw,input integer aa,input integer ad,input bit bw,input bit br,input integer ba,input integer bd);
 reg [1:0] want;
 begin
  @(negedge clk);a_write=aw;a_addr=11'(aa);a_data=2'(ad);b_write=bw;b_read=br;b_addr=11'(ba);b_data=2'(bd);
  want=br&&!bw ? expected[ba]:held;
  @(posedge clk);#1;
  if((br&&!bw)||known)begin
   if(b_q!==want)$fatal(1,"SCALE_UNIT_MISMATCH cycle=%0d A=%0d/%0d/%0d B=%0d/%0d/%0d/%0d expected=%0d actual=%0d",clocks,aw,aa,ad,bw,br,ba,bd,want,b_q);
  end
  if(br&&!bw)begin held=want;known=1;end
  else if(known)holds++;
  if(aw&&br&&aa==ba&&!bw)collisions++;
  if(aw&&bw&&aa!=ba)dual_writes++;
  if(aw&&bw&&aa==ba)priority_writes++;
  if(aw)expected[aa]=2'(ad);
  if(bw)expected[ba]=2'(bd);
  clocks++;
 end endtask
 initial begin
  // No cold output/RAM value is asserted. Initialize every valid word first.
  #110;
  for(integer i=0;i<1350;i++)step(1,i,i%4,0,0,0,0);
  step(0,0,0,0,1,0,0);
  for(integer datum=0;datum<4;datum++)for(integer i=0;i<1350;i++)begin
   // Common-clock A write/B read: B must see OLD data on this edge.
   step(1,i,datum,0,1,i,0);
   step(0,0,0,0,1,i,0);
  end
  for(integer i=0;i<1350;i++)begin
   step(1,(i+1)%1350,(i+2)%4,1,0,i,(i+3)%4);
   step(0,0,0,0,1,i,0);
   step(0,0,0,0,1,(i+1)%1350,0);
  end
  for(integer datum=0;datum<4;datum++)for(integer i=0;i<1350;i++)begin
   step(1,i,datum,1,0,i,(datum+1)%4);
   step(0,0,0,0,1,i,0);
  end
  repeat(32)step(0,0,0,0,0,0,0);
  $display("TEST_PASS_SCALE_UNIT clocks=%0d old_data_collisions=%0d distinct_dual_writes=%0d same_address_priority=%0d held_outputs=%0d",clocks,collisions,dual_writes,priority_writes,holds);
  $finish;
 end
 initial begin #1000000;$fatal(1,"SCALE_UNIT_WATCHDOG");end
endmodule
