`timescale 1ns/1ps
// Measure current single-write controller on the saved full JPEG pixel trace.
// No decoder, packet ingest, scanout reads or FPGA hardware are included.
module tb_sdram_throughput;
 reg clk=0;always #5 clk=~clk;
 wire read_clk;assign #2.75 read_clk=~clk;
 reg reset=1,valid=0;reg[23:0] address=0;reg[15:0] data=0;
 wire ready,rv,idle;wire[15:0] rd;wire[12:0] a;wire[1:0] ba,cke,cs;wire[15:0] dq;
 wire sclk,ras,cas,we,ldqm,udqm;
 integer mode;
 wire tile_in_ready,tile_out_valid,tile_first,tile_last,tile_fault;
 wire[23:0] tile_address;wire[15:0] tile_data;
 moonbub_tile_transpose tile(.clk(clk),.reset(reset),.abort(1'b0),
 .in_valid(valid && mode==2),.in_ready(tile_in_ready),.in_address(address),.in_data(data),
 .out_valid(tile_out_valid),.out_ready(ready),.out_address(tile_address),.out_data(tile_data),
 .out_burst_first(tile_first),.out_burst_last(tile_last),.fault(tile_fault));
 moonshine_sdram #(.POWERUP_CYCLES(20000),.REFRESH_CYCLES(750)) dut(
 .clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(mode==2 ? tile_out_valid : valid),.request_ready(ready),
 .request_write(1'b1),.request_address(mode==2 ? tile_address : address),.request_data(mode==2 ? tile_data : data),.response_valid(rv),
 .response_data(rd),.idle(idle),.sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),
 .sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),
 .sdram_ldqm(ldqm),.sdram_udqm(udqm));
 sdram_model model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(ldqm),.udqm(udqm),.dq(dq));
 reg[23:0] trace_addr[0:345599];reg[15:0] trace_data[0:345599];
 integer fd,n,i,idx,value,x,y,original_cycles,sorted_cycles,tile_cycles,writes_before,refresh_before;
 integer cycles=0,begin_cycle,src;
 reg[2047:0] trace_name;
 always @(posedge clk)cycles<=cycles+1;
 initial begin
  if(!$value$plusargs("TRACE_FILE=%s",trace_name))trace_name="/ross-work/tile-study/decoded-rgb565.txt";
  fd=$fopen(trace_name,"r");if(!fd)$fatal(1,"missing trace");
  for(i=0;i<345600;i=i+1)begin
   n=$fscanf(fd,"%d %h\n",idx,value);if(n!=2)$fatal(1,"truncated trace");
   x=idx%720;y=idx/720;trace_addr[i]=24'h080000+(x+40)*480+y;trace_data[i]=value;
  end
  $fclose(fd);
  for(mode=0;mode<3;mode=mode+1)begin
   reset=1;valid=0;
   for(i=0;i<345600;i=i+1)model.mem[trace_addr[i]]=~trace_data[i];
   repeat(5)@(negedge clk);reset=0;while(!ready)@(negedge clk);
   begin_cycle=cycles;writes_before=model.writes;refresh_before=model.refreshes;
   for(i=0;i<345600;i=i+1)begin
    src=(mode==1)?((i/64)*64+(i%8)*8+(i%64)/8):i;
    @(negedge clk);valid=1;address=trace_addr[src];data=trace_data[src];
    while(!(mode==2 ? tile_in_ready : ready))@(negedge clk);
   end
   @(negedge clk);valid=0;while(!idle || (mode==2 && (tile_out_valid || !tile_in_ready)))@(negedge clk);
   if(mode==2 && tile_fault)$fatal(1,"coalescer fault");
   if(model.writes-writes_before!=345600)$fatal(1,"write conservation failure mode=%0d actual=%0d",mode,model.writes-writes_before);
   for(i=0;i<345600;i=i+1)
    if(model.mem[trace_addr[i]]!==trace_data[i])$fatal(1,"pixel mismatch mode=%0d index=%0d",mode,i);
   if(mode==0)original_cycles=cycles-begin_cycle;else if(mode==1)sorted_cycles=cycles-begin_cycle;else tile_cycles=cycles-begin_cycle;
   $display("TRACE_RESULT mode=%0d cycles=%0d writes=%0d refreshes=%0d",mode,cycles-begin_cycle,model.writes-writes_before,model.refreshes-refresh_before);
  end
  $display("TEST_PASS_SDRAM_TRACE original_cycles=%0d sorted_cycles=%0d tile_cycles=%0d",original_cycles,sorted_cycles,tile_cycles);$finish;
 end
 initial begin #250000000;$fatal(1,"throughput watchdog");end
endmodule
