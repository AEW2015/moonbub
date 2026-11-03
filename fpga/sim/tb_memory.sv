`timescale 1ns/1ps
module tb_memory;
 reg clk=0;always #5 clk=!clk;
 wire read_clk;assign #2.75 read_clk=~clk;
 reg reset=1,pv=0,lr=0;wire pr,lready,ldv,idle;
 reg[23:0]pa=24'h080000,la=19200;reg[15:0]pd=16'hf800;wire[15:0]ld;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,lm,um;
 moonshine_memory dut(.clk(clk),.read_clk(read_clk),.reset(reset),.pixel_valid(pv),.pixel_ready(pr),.pixel_address(pa),.pixel_rgb565(pd),
 .line_req_valid(lr),.line_req_ready(lready),.line_req_address(la),.line_data_valid(ldv),.line_data(ld),.idle(idle),
 .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),
 .sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
 sdram_model model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 integer i,cycles=0,accepted=0,words=0,startcycle,linecycles,maxlinecycles=0;
 always @(posedge clk)begin
  cycles<=cycles+1;
  if(pv&&pr)begin pa<=pa+1;pd<=pd+1;accepted<=accepted+1;end
 end
 task read_line(input integer number);
 begin
  @(negedge clk);la=number*480;lr=1;
  while(!lready)@(negedge clk);
  @(negedge clk);lr=0;words=0;startcycle=cycles;
  while(words<480)begin
   if(pr)$fatal(1,"decoder accepted during line ownership");
   @(negedge clk);if(ldv)begin
    if(ld!==(16'h1000+number+words))$fatal(1,"line %d word %d actual %x",number,words,ld);
    words=words+1;
   end
  end
  linecycles=cycles-startcycle;if(linecycles>maxlinecycles)maxlinecycles=linecycles;
  if(linecycles>1842)$fatal(1,"scan line deadline missed %d",linecycles);
 end endtask
 initial begin
  for(i=0;i<480;i=i+1)begin model.mem[19200+i]=16'h1000+40+i;model.mem[19680+i]=16'h1000+41+i;end
  repeat(8)@(negedge clk);reset=0;pv=1;
  while(accepted<20)@(negedge clk);
  read_line(40);repeat(40)@(negedge clk);read_line(41);
  while(accepted<40)@(negedge clk);pv=0;while(!idle)@(negedge clk);
  if(model.writes!=accepted)$fatal(1,"write conservation %d %d",model.writes,accepted);
  for(i=0;i<accepted;i=i+1)if(model.mem[24'h080000+i]!==16'hf800+i)$fatal(1,"decoder write lost %d",i);
  for(i=0;i<480;i=i+1)if(model.mem[19200+i]!==16'h1000+40+i)$fatal(1,"front buffer overwritten");
  $display("MEMORY_PASS linewords960 concurrentwrites%0d maxlinecycles%0d deadline1842 refreshes%0d frontbuffer_preserved=1",accepted,maxlinecycles,model.refreshes);$finish;
 end
 initial begin #1000000;$fatal(1,"timeout");end
endmodule
