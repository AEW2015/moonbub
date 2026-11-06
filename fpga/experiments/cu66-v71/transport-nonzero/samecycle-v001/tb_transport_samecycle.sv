`timescale 1ns/1ps
module tb_transport_samecycle;
reg clk100=0,rst=0,reconfigure_required=0;reg[31:0]transport_gray=0;
always #5 clk100=~clk100;
wire mismatch,old_fault,new_fault,old_nonzero,new_nonzero;wire[97:0]old_history,new_history;
transport_samecycle_miter dut(.*);
integer cycles=0,reset_cycles=0,random_cycles=0;reg check_known=1;reg[31:0]rng=32'h91713579,number;integer i;
task step(input[31:0]gray,input reset,input q);begin
 transport_gray=gray;rst=reset;reconfigure_required=q;
 @(posedge clk100);#0.001;cycles=cycles+1;if(reset)reset_cycles=reset_cycles+1;
 if(old_history!==new_history)$fatal(1,"counter/meta/sync/quarantine history differs cycle%0d",cycles);
 if(check_known && mismatch!==0)$fatal(1,"same-edge fault/nonzero mismatch cycle%0d old%h new%h history%h",cycles,old_fault,new_fault,old_history);
 @(negedge clk100);
end endtask
initial begin
 #1;step(0,1,0);step(0,1,0);
 // Quarantine has no transport-reset branch in actual selected top.
 step(0,1,1);step(0,1,1);if(new_fault!==1||new_nonzero!==0)$fatal(1,"quarantine incorrectly cleared by rst");
 step(0,1,0);if(new_fault!==1)$fatal(1,"quarantine old first-stage sample lost");
 step(0,1,0);if(new_fault!==0)$fatal(1,"quarantine did not clear after original two edges");
 step(1,0,0);if(new_nonzero!==0)$fatal(1,"flag used first-stage/input early edge1");
 step(1,0,0);if(new_nonzero!==0)$fatal(1,"flag used first-stage early edge2");
 step(1,0,0);if(new_nonzero!==1)$fatal(1,"flag delayed versus registered counter edge3");
 step(0,0,0);if(new_nonzero!==1)$fatal(1,"clear early1");step(0,0,0);if(new_nonzero!==1)$fatal(1,"clear early2");step(0,0,0);if(new_nonzero!==0)$fatal(1,"clear late/sticky");
 for(i=0;i<32;i=i+1)begin step(32'b1<<i,0,0);step(32'b1<<i,0,0);step(32'b1<<i,0,0);if(new_nonzero!==1)$fatal(1,"onehotzero");end
 for(i=0;i<32;i=i+1)begin step(~(32'b1<<i),0,0);step(~(32'b1<<i),0,0);step(~(32'b1<<i),0,0);end
 number=32'hfffffff0;for(i=0;i<40;i=i+1)begin step(number^(number>>1),0,i[0]);number=number+1;end
 for(i=0;i<50000;i=i+1)begin
 rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);
 step(rng,rng[7:0]==8'h7a,rng[9]);random_cycles=random_cycles+1;
 end
 step(0,1,0);step(0,1,0);step(0,0,0);
 // Explicitly NOT a four-state-X equivalence claim: XOR pessimism differs.
 check_known=0;step(32'h000x0001,0,0);step(32'h000x0001,0,0);step(32'h000x0001,0,0);
 if(old_fault!==1'bx||new_fault!==1'b1||old_nonzero!==1'bx||new_nonzero!==1'b1)$fatal(1,"expected disclosed four-state difference not observed");
 $display("FOUR_STATE_SCOPE_EXPECTED_DIFFERENCE old_fault=X new_fault=1 gray=000x0001 quarantine=0");
 step(0,1,0);check_known=1;step(0,1,0);step(0,0,0);
 $display("TRANSPORT_SAME_EDGE_PASS cycles=%0d random=%0d reset_edges=%0d counter_histories_exact=1 quarantine_reset_history_exact=1 first_stage_not_used=1 third_edge_assert_and_clear=1 max_fanout_not_measured=1 four_state_equivalence=0",cycles,random_cycles,reset_cycles);$finish;
end
initial begin #1000000;$fatal(1,"watchdog");end
endmodule
