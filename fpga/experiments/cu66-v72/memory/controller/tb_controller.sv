`timescale 1ns/1ps
module tb_controller #(parameter real TAC_NS=2.0);
 logic clk=0,read_clk=0,reset=1;
 always #5 clk=~clk;
 always @(clk)read_clk<=#2.75 ~clk;
 logic request_valid=0,request_ready,request_write=0;
 logic[23:0]request_address=0;
 logic[127:0]request_burst_data=0;
 logic[15:0]request_byte_enable=0;
 logic response_valid,idle;logic[15:0]response_data;
 wire[12:0]sdram_a;wire[1:0]sdram_bs,sdram_cke,sdram_cs_n;
 wire[15:0]sdram_dq;wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 cu72_sdram_controller #(.POWERUP_CYCLES(20))dut(.*);
 cu72_sdram_model #(.T_AC_NS(TAC_NS))model(.clk(sdram_clk),.reset,.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 integer cycles=0,checks=0,write_transactions=0,read_transactions=0,reset_probes=0,reset_edge_probes=0,held_request_clocks=0;
 integer seed=7201,refresh_observed=0,refresh_previous=0;
 logic[23:0]addresses[0:15];logic[15:0]expected[0:127];
 logic[15:0]mask_cases[0:7];
 always @(posedge clk)begin
  cycles=cycles+1;
  if(!reset&&request_valid&&!request_ready)held_request_clocks=held_request_clocks+1;
  if(model.refreshes>refresh_previous)refresh_observed=refresh_observed+model.refreshes-refresh_previous;
  refresh_previous=model.refreshes;
 end
 function automatic logic[127:0]pattern(input integer salt);
  for(integer j=0;j<8;j=j+1)pattern[j*16+:16]=16'(salt*37+j*107+seed);
 endfunction
 task automatic launch(input bit writing,input logic[23:0]address,input logic[127:0]data,input logic[15:0]enable);
  integer wait_count;
  begin
   @(negedge clk);request_valid=1;request_write=writing;request_address=address;request_burst_data=data;request_byte_enable=enable;wait_count=0;
   do begin @(posedge clk);wait_count=wait_count+1;if(wait_count>200)$fatal(1,"request handshake watchdog");end while(!request_ready);
   @(negedge clk);request_valid=0;
   // Payload no longer belongs to the controller input after acceptance.
   request_address=24'hfffff8;request_burst_data=~data;request_byte_enable=~enable;
  end
 endtask
 task automatic write_block(input integer block_id,input logic[127:0]data,input logic[15:0]enable);
  integer before_words,before_beats,before_commands,n,started,lastj;logic[23:0]old_trace_address;logic[15:0]old_trace_data;
  begin
   before_words=model.writes;before_beats=model.write_bus_beats;before_commands=model.write_commands;started=cycles;old_trace_address=model.last_write_address;old_trace_data=model.last_write_data;
   launch(1,addresses[block_id],data,enable);
   while(!idle)begin @(negedge clk);if(response_valid)$fatal(1,"write produced read response");if(cycles-started>200)$fatal(1,"write drain watchdog");end
   if(model.write_bus_beats-before_beats!=8||model.write_commands-before_commands!=1)$fatal(1,"write idle before complete BL8");
   if(model.cycle-model.lastwrite[addresses[block_id][23:22]]<2)$fatal(1,"write idle before final tWR");
   n=0;lastj=0;
   for(integer j=0;j<8;j=j+1)begin
    if(enable[2*j])expected[block_id*8+j][7:0]=data[j*16+:8];
    if(enable[2*j+1])expected[block_id*8+j][15:8]=data[j*16+8+:8];
    if(enable[2*j]||enable[2*j+1])begin n=n+1;lastj=j;end
   end
   if(model.writes-before_words!=n)$fatal(1,"active word count mismatch");
   if(n>0)begin if(model.last_write_address!==addresses[block_id]+24'(lastj)||model.last_write_data!==expected[block_id*8+lastj])$fatal(1,"write event trace mismatch");end
   else if(model.last_write_address!==old_trace_address||model.last_write_data!==old_trace_data)$fatal(1,"masked noop changed write trace");
   checks=checks+4;write_transactions=write_transactions+1;
  end
 endtask
 task automatic read_block(input integer block_id);
  integer word_no,started;
  begin
   launch(0,addresses[block_id],0,0);word_no=0;started=cycles;
   while(word_no<8)begin
    @(negedge clk);
    if(response_valid)begin
     if(response_data!==expected[block_id*8+word_no])$fatal(1,"read mismatch block%0d word%0d got%h expected%h",block_id,word_no,response_data,expected[block_id*8+word_no]);
     word_no=word_no+1;checks=checks+1;
    end
    if(cycles-started>200)$fatal(1,"read burst watchdog");
   end
   @(negedge clk);if(response_valid)$fatal(1,"read response longer than8 beats");
   read_transactions=read_transactions+1;
  end
 endtask
 logic[127:0]data;
 integer before_beats,prefix,started;
 initial begin
  if(!$value$plusargs("SEED=%d",seed))$fatal(1,"SEED plusarg required");
  addresses[0]=24'h080000;addresses[1]=24'h080008;
  addresses[2]=24'h0801f8;addresses[3]=24'h080200;
  addresses[4]=24'h3ffff8;addresses[5]=24'h400000;
  addresses[6]=24'h7ffff8;addresses[7]=24'h800000;
  addresses[8]=24'hbffff8;addresses[9]=24'hc00000;
  addresses[10]=24'hfffff8;addresses[11]=24'hfffdf8;
  addresses[12]=24'h100000;addresses[13]=24'h500000;
  addresses[14]=24'h900000;addresses[15]=24'hc80000;
  mask_cases[0]=16'h00ff;mask_cases[1]=16'hff00;mask_cases[2]=16'h5555;mask_cases[3]=16'haaaa;
  mask_cases[4]=16'h0001;mask_cases[5]=16'h8000;mask_cases[6]=16'h0000;mask_cases[7]=16'hffff;
  repeat(5)@(negedge clk);reset=0;
  // First request is deliberately held through initialization and refresh.
  for(integer b=0;b<16;b=b+1)begin
   write_block(b,pattern(100+b),16'hffff);read_block(b);
  end
  // Partial/byte/no-op masks preserve every other byte and neighboring block.
  for(integer m=0;m<8;m=m+1)begin
   for(integer b=0;b<16;b=b+1)begin
    write_block(b,pattern(1000+m*16+b),mask_cases[m]);read_block(b);
    if(b<2)read_block(1-b);
   end
  end
  // Let refresh run without traffic, then alternate row/bank conflicts.
  repeat(2300)@(negedge clk);
  for(integer n=0;n<32;n=n+1)begin
   write_block((n*7)%16,pattern(3000+n),16'hffff);read_block((n*7)%16);
  end
  if(refresh_observed<5)$fatal(1,"refresh not exercised");
  if(held_request_clocks<20)$fatal(1,"held request not exercised");
  // Reset at every accepted write prefix, including pre-command and recovery.
  for(prefix=0;prefix<=8;prefix=prefix+1)begin
   write_block(0,pattern(4000+prefix),16'hffff);
   before_beats=model.write_bus_beats;data=pattern(5000+prefix);
   launch(1,addresses[0],data,16'hffff);started=cycles;
   while(model.write_bus_beats-before_beats<prefix)begin
    @(negedge clk);if(cycles-started>100)$fatal(1,"reset prefix watchdog");
   end
   if(model.write_bus_beats-before_beats!=prefix)$fatal(1,"reset prefix not exact");
   for(integer j=0;j<prefix;j=j+1)expected[j]=data[j*16+:16];
   reset=1;request_valid=0;repeat(5)@(negedge clk);reset=0;
   while(!idle)@(negedge clk);
   repeat(12)begin @(negedge clk);if(response_valid)$fatal(1,"orphan response after reset");end
   read_block(0);write_block(0,pattern(6000+prefix),16'hffff);read_block(0);
   reset_probes=reset_probes+1;
  end
  // Assert reset between edges while idle and a new request is valid. No
  // caller may see an acceptance or quiescence indication under reset.
  while(!idle)@(negedge clk);
  @(negedge clk);request_valid=1;request_write=1;request_address=addresses[1];
  request_burst_data=pattern(7777);request_byte_enable=16'hffff;reset=1;
  #0.001;if(request_ready||idle)$fatal(1,"asynchronous reset did not gate ready/idle");checks=checks+1;
  @(posedge clk);#0.001;if(request_ready||idle)$fatal(1,"reset clock exposed ready/idle");checks=checks+1;
  repeat(5)@(negedge clk);request_valid=0;reset=0;
  while(!idle)@(negedge clk);
  read_block(1);write_block(1,pattern(8888),16'hffff);read_block(1);reset_edge_probes=reset_edge_probes+1;
  if(reset_probes!=9||reset_edge_probes!=1||write_transactions!=195||read_transactions!=212)$fatal(1,"terminal counts writes%0d reads%0d resets%0d",write_transactions,read_transactions,reset_probes);
  $display("CONTROLLER_V72_PASS seed=%0d checks=%0d writes=%0d reads=%0d reset_probes=%0d reset_edge_probes=%0d mask_cases=8 held_request_clocks=%0d refreshes_observed=%0d cycles=%0d",seed,checks,write_transactions,read_transactions,reset_probes,reset_edge_probes,held_request_clocks,refresh_observed,cycles);
  $finish;
 end
 initial begin #10000000;$fatal(1,"controller overall watchdog");end
endmodule
