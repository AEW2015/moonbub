// Simulator 5.020 event-scheduling workaround; cross-check against original XSim bench.
`timescale 1ns/1ps
// Actual display line fetch + memory arbiter/controller; decoder/QSPI omitted.
module tb_burst_memory_throughput;
 reg clk=0,pclk=0;always #5 clk=~clk;always #17.029 pclk=~pclk;
 reg read_clk;always @(clk) read_clk <= #2.75 ~clk;
 reg reset=1,valid=0;reg[23:0] address=0;reg[15:0] data=0;
 integer mode=1;wire protocol_fault;wire tile_in_ready,tile_out_valid,tile_first,tile_last,tile_fault;
 wire[23:0] tile_address;wire[15:0] tile_data;wire pixel_ready,mem_idle;
 wire line_req,line_ready,line_valid,frame_boundary;wire[23:0] line_address;wire[15:0]line_data;
 wire[31:0]underruns;wire hs,vs,de;wire[9:0] px,py;wire[7:0] red,green,blue;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,ldqm,udqm;
 moonbub_tile_transpose tile(.clk(clk),.reset(reset),.abort(1'b0),
 .in_valid(valid && mode==1),.in_ready(tile_in_ready),.in_address(address),.in_data(data),
 .out_valid(tile_out_valid),.out_ready(pixel_ready),.out_address(tile_address),.out_data(tile_data),
 .out_burst_first(tile_first),.out_burst_last(tile_last),.fault(tile_fault));
 moonshine_memory_burst memory(.clk(clk),.read_clk(read_clk),.reset(reset),
 .pixel_valid(mode==1 ? tile_out_valid : valid),.pixel_ready(pixel_ready),
 .pixel_address(mode==1 ? tile_address : address),.pixel_rgb565(mode==1 ? tile_data : data),
 .line_req_valid(line_req),.line_req_ready(line_ready),.line_req_address(line_address),
 .line_data_valid(line_valid),.line_data(line_data),.idle(mem_idle),.protocol_fault(protocol_fault),.sdram_a(a),.sdram_bs(ba),
 .sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),
 .sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(ldqm),.sdram_udqm(udqm));
 moonshine_lcd lcd(.pixel_clk(pclk),.reset_n(!reset),.mem_clk(clk),.mem_reset(reset),
 .front_valid(1'b1),.front_buffer(1'b0),.pattern_enable(1'b0),.line_req_valid(line_req),
 .line_req_ready(line_ready),.line_req_address(line_address),.line_data_valid(line_valid),
 .line_data(line_data),.frame_boundary(frame_boundary),.underruns(underruns),.hsync(hs),.vsync(vs),
 .data_enable(de),.physical_x(px),.physical_y(py),.red(red),.green(green),.blue(blue));
 sdram_model_burst model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(ldqm),.udqm(udqm),.dq(dq));
 reg[23:0] trace_addr[0:345599];reg[15:0]trace_data[0:345599];
 integer fd,n,i,idx,value,x,y,cycles=0,begin_cycle,writes_before,underruns_before,frames_seen=0,frames_before;
 integer pixel_count=345600, warmup_cycles=2000000, phase=0;
 reg[2047:0] trace_name;
 always @(posedge clk)begin cycles<=cycles+1;if(frame_boundary)frames_seen<=frames_seen+1;end
 initial begin
  if ($value$plusargs("PIXELS=%d",pixel_count)) begin end
  if ($value$plusargs("WARMUP_CYCLES=%d",warmup_cycles)) begin end
  if(pixel_count<64 || pixel_count>345600 || pixel_count%64!=0 || warmup_cycles<0)
   $fatal(1,"invalid pixel_count/warmup %0d/%0d",pixel_count,warmup_cycles);
  $display("MEMORY_PROGRESS begin pixels=%0d warmup_cycles=%0d",pixel_count,warmup_cycles);$fflush();
  // Defined front-buffer contents; this test observes timing, not image quality.
  for(i=0;i<384000;i=i+1)model.mem[i]=0;
  if(!$value$plusargs("TRACE_FILE=%s",trace_name))trace_name="/ross-work/burst-memory/decoded-rgb565.txt";
  fd=$fopen(trace_name,"r");if(!fd)$fatal(1,"missing trace");
  for(i=0;i<pixel_count;i=i+1)begin
   n=$fscanf(fd,"%d %h\n",idx,value);if(n!=2)$fatal(1,"truncated trace");
   x=idx%720;y=idx/720;trace_addr[i]=24'h080000+(x+40)*480+y;trace_data[i]=value;
  end
  $fclose(fd);$display("MEMORY_PROGRESS trace_loaded time=%0t",$time);$fflush();
  for(mode=1;mode<2;mode=mode+1)begin
   reset=1;valid=0;
   // Poison every back-buffer location so stale pixels cannot pass readback.
   for(i=0;i<pixel_count;i=i+1)model.mem[trace_addr[i]]=~trace_data[i];
   phase=1;$display("MEMORY_PROGRESS mode=%0d reset time=%0t",mode,$time);$fflush();
   repeat(5)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);
   phase=2;$display("MEMORY_PROGRESS mode=%0d idle time=%0t",mode,$time);$fflush();
   // Warm LCD and line buffers for more than a display refresh before timing.
   repeat(warmup_cycles)@(negedge clk);
   phase=3;$display("MEMORY_PROGRESS mode=%0d warm time=%0t",mode,$time);$fflush();
   begin_cycle=cycles;writes_before=model.writes;underruns_before=underruns;frames_before=frames_seen;
   for(i=0;i<pixel_count;i=i+1)begin
    if(i!=0 && i%65536==0)begin $display("MEMORY_PROGRESS mode=%0d accepted=%0d time=%0t",mode,i,$time);$fflush();end
    @(negedge clk);valid=1;address=trace_addr[i];data=trace_data[i];
    while(!(mode==1 ? tile_in_ready : pixel_ready))@(negedge clk);
   end
   phase=4;@(negedge clk);valid=0;while(!mem_idle || (mode==1 && (tile_out_valid || !tile_in_ready)))@(negedge clk);
   if(mode==1 && tile_fault)$fatal(1,"coalescer fault");
   if(protocol_fault)$fatal(1,"burst staging fault");
   if(model.writes-writes_before!=pixel_count)$fatal(1,"write conservation failure");
   for(i=0;i<pixel_count;i=i+1)
    if(model.mem[trace_addr[i]]!==trace_data[i])$fatal(1,"pixel mismatch mode=%0d index=%0d",mode,i);
   $display("BURST_MEMORY_RESULT mode=%0d cycles=%0d writes=%0d scanout_underruns=%0d display_boundaries=%0d",mode,cycles-begin_cycle,model.writes-writes_before,underruns-underruns_before,frames_seen-frames_before);
  end
  $display("TEST_PASS_BURST_MEMORY_TRACE");$finish;
 end
 initial begin #500000000;$fatal(1,"memory throughput watchdog phase=%0d mode=%0d index=%0d",phase,mode,i);end
endmodule
