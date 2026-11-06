`timescale 1ns/1ps
module tb_event;
 reg clk=0,rst=0;reg[7:0]event_code=0,stage=0,fatal_code=0;
 reg[23:0]last_address=0;reg[31:0]event_fid=0;reg[63:0]event_generation=0,clock_count=0;reg[9:0]diag_address=0;
 wire[31:0]old_data,new_data,old_seq,new_seq,old_over,new_over;
 event_old ref_ring(.clk,.rst,.event_code,.stage,.fatal_code,.last_address,.event_fid,.event_generation,.clock_count,.diag_address,.diag_data(old_data),.event_sequence(old_seq),.event_overwrites(old_over));
 event_new dut(.clk,.rst,.event_code,.stage,.fatal_code,.last_address,.event_fid,.event_generation,.clock_count,.diag_address,.diag_data(new_data),.event_sequence(new_seq),.event_overwrites(new_over));
 integer checks=0,cycles=0;reg[31:0]seed=32'h715efe11;
 function automatic[31:0]rng(input[31:0]v);rng=v*32'd1664525+32'd1013904223;endfunction
 task check(input bit good,input string why);begin checks++;if(!good)$fatal(1,"%s cycle=%0d addr=%h old=%h new=%h",why,cycles,diag_address,old_data,new_data);end endtask
 task scan;begin
  check(old_seq===new_seq&&old_over===new_over,"same original-edge logical counters");
  for(integer a=0;a<1024;a++)begin diag_address=10'(a);#0.001;check(old_data===new_data,"all diagnostic indices exactfourstate");end
 end endtask
 task tick;begin #2;if(cycles>0)scan();#2;clk=1;#1;cycles++;scan();#4;clk=0;clock_count=clock_count+1;end endtask
 task data;begin
  seed=rng(seed);event_generation={seed,seed^32'hacbd1234};seed=rng(seed);event_fid=seed;seed=rng(seed);last_address=seed[23:0];stage=seed[31:24];seed=rng(seed);fatal_code=seed[7:0];
 end endtask
 initial begin
  // Startup physical payload is deliberately unknown/random. Only validity resets.
  for(integer i=0;i<8;i++)begin
   dut.events[i]='x;for(integer j=0;j<8;j++)begin seed=rng(seed);dut.events[i][32*j+:32]=seed;end
   dut.events[i][i*16+:16]='x;
  end
  rst=1;event_code=10;data();tick();
  for(integer a=256;a<512;a++)begin diag_address=10'(a);#0.001;check(new_data===0,"freshresetzerosdespiteunknownpayload");end
  rst=0;event_code=0;tick();
  for(integer n=0;n<24;n++)begin event_code=8'(1+n%10);data();tick();end
  event_code=0;tick();tick();
  // Natural32-bit counter/pointer wrap, including original overwrite-wrap behavior.
  ref_ring.event_sequence=32'hfffffff8;dut.event_sequence=32'hfffffff8;
  ref_ring.event_overwrites=32'hfffffffd;dut.event_overwrites=32'hfffffffd;
  for(integer n=0;n<32;n++)begin event_code=1;data();tick();end
  check(new_seq===32'd24,"sequencewrapexact");
  for(integer n=0;n<1200;n++)begin
   data();event_code=seed[3:0];rst=(n%97==0);
   if(n%23==0)event_code=0;
   if(n%41==0)event_code=8'hxx;
   if(n%43==0)begin event_code=9;event_fid[3:0]='x;event_generation[35:32]='x;last_address[7:4]='x;fatal_code[2:0]='x;end
   tick();
  end
  // Synchronous reset while a just-logical event is still awaiting physical write.
  rst=0;event_code=4;data();tick();check(dut.event_pending_valid,"pendingeventexists");
  rst=1;event_code=10;tick();check(new_seq===0&&new_over===0&&!dut.event_pending_valid,"resetdiscardspendingwithoutghost");
  rst=0;event_code=0;tick();tick();
  $display("EVENT_RETIME_FOURSTATE_PASS checks=%0d cycles=%0d",checks,cycles);$finish;
 end
endmodule
