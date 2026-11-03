`timescale 1ns/1ps
// Directed test of the exact longrun producer expression around 32-bit limits.
module tb_schedule64;
 integer f;longint unsigned epoch,actual,previous,expected;
 initial begin
  epoch=64'd4290000000; previous=0;
  for(f=0;f<1800;f=f+1)begin
   actual=epoch+(64'(f)*64'd10000000)/64'd3;
   expected=epoch+64'(f/3)*64'd10000000+64'((f%3)*10000000/3);
   if(actual!=expected || (f!=0 && actual<=previous))$fatal(1,"schedule f=%0d actual=%0d expected=%0d",f,actual,expected);
   previous=actual;
  end
  if(previous<=64'd8589934592)$fatal(1,"did not cross two 32-bit counter boundaries");
  $display("TEST_PASS_SCHEDULE64 frames=1800 last=%0d epoch=%0d",previous,epoch);$finish;
 end
endmodule
