`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;
reg reset=1,start_valid=0,in_valid=0,in_last=0,abort_valid=0,result_ready=0;
reg[63:0]start_owner=64'h1234,abort_owner=64'h1234;
reg[31:0]start_epoch=1,start_frame=0,start_bytes=17412;
reg[31:0]abort_epoch=1,abort_frame=0;reg[7:0]in_byte=0;
reg[7:0]fixture[0:17412-1];integer checks=0,results=0,seed=23,i,t,early_last=-1;
reference refdut(.clk(clk),.reset(reset),.start_valid(start_valid),.start_owner(start_owner),.start_epoch(start_epoch),.start_frame(start_frame),.start_bytes(start_bytes),.in_valid(in_valid),.in_byte(in_byte),.in_last(in_last),.abort_valid(abort_valid),.abort_owner(abort_owner),.abort_epoch(abort_epoch),.abort_frame(abort_frame),.result_ready(result_ready));
candidate candut(.clk(clk),.reset(reset),.start_valid(start_valid),.start_owner(start_owner),.start_epoch(start_epoch),.start_frame(start_frame),.start_bytes(start_bytes),.in_valid(in_valid),.in_byte(in_byte),.in_last(in_last),.abort_valid(abort_valid),.abort_owner(abort_owner),.abort_epoch(abort_epoch),.abort_frame(abort_frame),.result_ready(result_ready));
always @(posedge clk)begin #1;
 if({refdut.start_ready,refdut.in_ready,refdut.abort_rejected,refdut.result_valid,
 refdut.result_code,refdut.envelope_checked,refdut.payload_supported,refdut.component_magic_known,
 refdut.result_owner,refdut.result_epoch,refdut.result_frame,refdut.base_bytes,refdut.hud_bytes,refdut.received_bytes}
 !=={candut.start_ready,candut.in_ready,candut.abort_rejected,candut.result_valid,
 candut.result_code,candut.envelope_checked,candut.payload_supported,candut.component_magic_known,
 candut.result_owner,candut.result_epoch,candut.result_frame,candut.base_bytes,candut.hud_bytes,candut.received_bytes})
 $fatal(1,"Public output mismatch cycle %0d",checks);
 checks=checks+1;
end
task clear;begin @(negedge clk);reset=1;start_valid=0;in_valid=0;abort_valid=0;
 repeat(3)@(negedge clk);reset=0;end endtask
task launch;begin @(negedge clk);start_valid=1;while(!refdut.start_ready)@(negedge clk);
 @(negedge clk);start_valid=0;end endtask
task sendbytes(input integer count);integer j,guard;begin
 for(j=0;j<count;j=j+1)begin
  repeat(($random(seed)&3)==0?1:0)@(negedge clk);
  in_valid=1;in_byte=fixture[j];in_last=(j==17412-1||j==early_last);guard=0;
  @(posedge clk);while(!refdut.in_ready)begin @(posedge clk);guard=guard+1;if(guard>100000)$fatal(1,"stuck byte");end
  @(negedge clk);in_valid=0;
 end
end endtask
task expect_error(input integer code);integer guard;begin guard=0;
 while(!refdut.result_valid)begin @(negedge clk);guard=guard+1;if(guard>100000)$fatal(1,"missing error");end
 if(refdut.result_code!=code||refdut.envelope_checked)$fatal(1,"wrong error expected=%0d actual=%0d",code,refdut.result_code);
 repeat(3)@(negedge clk);result_ready=1;@(negedge clk);result_ready=0;
end endtask
task complete;integer guard;begin launch;sendbytes(17412);guard=0;
 while(!refdut.result_valid)begin @(negedge clk);guard=guard+1;if(guard>100000)$fatal(1,"stuck result");end
 if(refdut.result_code!=9||!refdut.envelope_checked)$fatal(1,"fixture rejected");
 results=results+1;repeat(7)@(negedge clk);result_ready=1;@(negedge clk);result_ready=0;
end endtask
initial begin $readmemh("fixture.hex",fixture);clear;complete;
 for(t=0;t<4;t=t+1)begin
  launch;case(t)0:sendbytes(25);1:sendbytes(45);2:sendbytes(53);3:sendbytes(170);endcase
  clear;repeat(11)@(negedge clk);complete;
 end
 launch;sendbytes(45);abort_valid=1;@(negedge clk);abort_valid=0;
 repeat(5)@(negedge clk);if(!refdut.result_valid||refdut.result_code!=8)$fatal(1,"abort missing");
 result_ready=1;@(negedge clk);result_ready=0;complete;
 launch;sendbytes(45);abort_owner=64'h9999;abort_valid=1;@(negedge clk);
 if(!refdut.abort_rejected)$fatal(1,"stale abort accepted");abort_valid=0;abort_owner=64'h1234;
 clear;complete;
 
 start_owner=0;launch;expect_error(1);start_owner=64'h1234;
 fixture[4]=2;launch;sendbytes(53);expect_error(2);$readmemh("fixture.hex",fixture);
 fixture[5]=fixture[5]^1;launch;sendbytes(53);expect_error(3);$readmemh("fixture.hex",fixture);
 fixture[100]=fixture[100]^1;launch;sendbytes(17412);expect_error(4);$readmemh("fixture.hex",fixture);
 $readmemh("badtag.hex",fixture);launch;sendbytes(17412);expect_error(5);$readmemh("fixture.hex",fixture);
 early_last=21;launch;sendbytes(22);expect_error(6);early_last=-1;
 complete;
 // Reset with a completed result held under backpressure, then recover.
 launch;sendbytes(17412);wait(refdut.result_valid);clear;complete;
 $display("RESET_TAG_NEGATIVE_RECOVERY_PASS reasons=1,2,3,4,5,6 held_result_reset=1");

 $display("RESET_TAG_EQUIVALENCE_PASS cycles=%0d valid_fixtures=%0d resets_in_header_body=4 matched_abort=1 stale_abort=1",checks,results);$finish;
end
initial begin #100000000;$fatal(1,"watchdog");end
endmodule
