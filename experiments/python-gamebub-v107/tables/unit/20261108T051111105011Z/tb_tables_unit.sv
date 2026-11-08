`timescale 1ns/1ps
module tb_tables_unit;
 reg clk=0;always #5 clk=~clk;
 reg a_write=0,b_write=0,b_read=0;
 reg [10:0] a_addr=0,b_addr=0;reg [1:0] a_data=0,b_data=0;
 wire [1:0] b_q;
 reg reset=0,start=0,abort_packet=0,mode_write=0,mode_read=0;
 reg [12:0]mode_address=0,mode_read_address=0;reg[1:0]mode_data=0;wire[1:0]mode_q;
 cu66_tables_unit_v107 dut(.*);
 reg[1:0]mode_expected[0:8099];reg[1:0]mode_held;reg mode_known=0;
 integer mode_clocks=0,mode_holds=0,mode_kills=0;
 task mode_step(input bit we,input integer address,input integer value,input bit re,input integer rd,input integer kills);
 reg [1:0]wanted;
 begin
  @(negedge clk);mode_write=we;mode_address=13'(address);mode_data=2'(value);mode_read=re;mode_read_address=13'(rd);
  reset=(kills&1)!=0;start=(kills&2)!=0;abort_packet=(kills&4)!=0;
  wanted=re&&!we&&kills==0 ? mode_expected[rd]:mode_held;
  @(posedge clk);#1;
  if((re&&!we&&kills==0)||mode_known)if(mode_q!==wanted)$fatal(1,"MODE_UNIT_MISMATCH clock=%0d expected=%0d actual=%0d",mode_clocks,wanted,mode_q);
  if(re&&!we&&kills==0)begin mode_held=wanted;mode_known=1;end else if(mode_known)mode_holds++;
  if(we&&kills==0)mode_expected[address]=2'(value);
  if(kills!=0)mode_kills++;
  mode_clocks++;
 end endtask
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
  for(integer i=0;i<8100;i++)mode_step(1,i,i%4,0,0,0);
  mode_step(0,0,0,1,123,0);
  for(integer value=0;value<4;value++)begin
   for(integer i=0;i<8100;i++)mode_step(1,i,value,1,123,0);
   for(integer i=0;i<8100;i++)mode_step(0,0,0,1,i,0);
  end
  for(integer flags=1;flags<8;flags++)begin
   mode_step(1,0,3,1,0,flags);
   mode_step(0,0,0,1,0,0);
  end
  repeat(32)mode_step(0,0,0,0,0,0);
  $display("TEST_PASS_MODE_UNIT clocks=%0d held_outputs=%0d cancelled=%0d",mode_clocks,mode_holds,mode_kills);
  $display("TEST_PASS_SCALE_UNIT clocks=%0d old_data_collisions=%0d distinct_dual_writes=%0d same_address_priority=%0d held_outputs=%0d",clocks,collisions,dual_writes,priority_writes,holds);
   $display("TEST_PASS_TABLES_UNIT");
  $finish;
 end
 initial begin #2000000;$fatal(1,"SCALE_UNIT_WATCHDOG");end
endmodule
