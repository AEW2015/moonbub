`timescale 1ns/1ps
module tb_collisions;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,bw=0;reg[11:0]addr=0;reg[31:0]wd=0;wire[31:0]rd;
 ar03_fixture_diagnostic dut(.clk(clk),.reset(reset),.bus_write(bw),.bus_address(addr),.bus_wdata(wd),.bus_rdata(rd));
 integer c,checks=0,accepted_starts=0;reg[63:0]saved_owner;
 always @(posedge clk)if(reset)accepted_starts=0;
 else if(dut.compute.start_valid&&dut.compute.start_ready)accepted_starts=accepted_starts+1;
 task command(input[31:0]value);begin @(negedge clk);bw=1;addr='h408;wd=value;@(negedge clk);bw=0;end endtask
 task clean_reset;begin @(negedge clk);reset=1;bw=0;repeat(4)@(negedge clk);reset=0;repeat(2)@(negedge clk);end endtask
 initial begin
  for(c=0;c<9;c=c+1)begin
   clean_reset();
   if(c==1)force dut.ks=0;
   command(1);
   if(c>1)begin wait(dut.state==2);@(negedge clk);end
   // Seed visibly distinct held counters/result identity before the STOP edge.
   dut.elapsed=41;dut.samples=17;dut.bytes_sent=23;dut.result_sequence=7;
   dut.result_epoch=55;dut.result_frame=66;dut.result_tag=128'h123456;
   saved_owner=dut.owner;
   if(c<2)begin
    if(dut.state!==1||dut.compute.start_valid!==1||dut.compute.start_ready!==(c==0)||accepted_starts!==0)$fatal(1,"START pre-STOP handshake setup c%0d ready%b accepted%0d",c,dut.compute.start_ready,accepted_starts);
    checks=checks+1;
   end
   if(c==2||c==7)begin force dut.byte_valid=1;force dut.ki=1;end
   if(c==3||c==7)force dut.sv=1;
   if(c==4||c==5||c==7)begin force dut.cv=1;force dut.co=64'd1;force dut.ce=32'd1;force dut.cf=32'd99;force dut.ct=128'habcdef;end
   if(c==5)force dut.co=64'hdeadbeef00000001;
   if(c==6||c==7)begin force dut.ev=1;force dut.es=4'd8;force dut.ec=8'd3;end
   if(c==8)begin force dut.byte_valid=1;force dut.ki=0;end
   bw=1;addr='h408;wd=2;
   #1;
   if(dut.cancel!==0||dut.compute.abort!==0)$fatal(1,"raw STOP still reaches private abort c%0d",c);
   if(c<2&&dut.compute.start_valid!==1)$fatal(1,"raw STOP masks private START");
   if(c>=2&&dut.compute.completion_ready!==1)$fatal(1,"raw STOP masks completion ready");
   @(posedge clk);#1;
   if(dut.state!==5||dut.cancel!==1||dut.compute.abort!==1)$fatal(1,"registered CANCEL edge c%0d",c);
   if(c<2)begin
    if(accepted_starts!==(c==0?1:0))$fatal(1,"STOP-edge START acceptance c%0d accepted%0d",c,accepted_starts);
    checks=checks+1;
   end
   if(dut.elapsed!==41||dut.samples!==17||dut.bytes_sent!==23||dut.result_sequence!==7||dut.owner!==saved_owner||dut.result_epoch!==55||dut.result_frame!==66||dut.result_tag!==0||dut.fault_stage!==0||dut.fault_code!==0)$fatal(1,"STOP published event/counter/result c%0d",c);
   checks=checks+1;
   @(negedge clk);bw=0;
   release dut.ks;release dut.byte_valid;release dut.ki;release dut.sv;release dut.cv;release dut.co;release dut.ce;release dut.cf;release dut.ct;release dut.ev;release dut.es;release dut.ec;
   @(posedge clk);#1;
   if(dut.state!==6||dut.byte_valid!==0||dut.cancel!==0)$fatal(1,"CANCEL failed drain c%0d",c);
   repeat(20)@(negedge clk);
   if(dut.result_sequence!==7||dut.result_tag!==0||dut.samples!==17||dut.bytes_sent!==23||dut.state!==6)$fatal(1,"late event escaped c%0d",c);
   command(4);if(dut.state!==0||dut.owner!==saved_owner||dut.result_sequence!==7)$fatal(1,"CLEAR identity c%0d",c);
   command(1);wait(dut.state==2);repeat(24)@(negedge clk);
   if(dut.owner!==2||dut.result_sequence!==7||dut.result_tag!==0||dut.fault_code!==0||dut.samples!==0)$fatal(1,"restart contaminated c%0d",c);
   command(2);repeat(3)@(negedge clk);if(dut.state!==6)$fatal(1,"second STOP c%0d",c);
   clean_reset();if(dut.owner!==0||dut.result_sequence!==0||dut.state!==0)$fatal(1,"reset c%0d",c);
   checks=checks+4;
  end
  $display("CANCEL_COLLISIONS_PASS cases=9 checks=%0d START_ready_blocked=1 byte_transfer_hold=1 sample=1 completion_good_bad=1 error=1 simultaneous_all=1 raw_STOP_no_private_abort=1 no_publication=1 next_CANCEL_abort=1 CLEAR_reset_restart=1",checks);$finish;
 end
 initial begin #100000;$fatal(1,"collision timeout");end
endmodule
