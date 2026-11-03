`timescale 1ns/1ps
module tb_staging_arbiter #(parameter integer LINES=24,LINE_PERIOD=1843,BACKGROUND_BURSTS=200,
                            CORRUPT_PAYLOAD=0,MISALIGN_REQUEST=0);
 localparam integer DISPLAY_BASE=40*480, PIXEL_BASE='h80000, JWRITE_BASE='h60000, JREAD_BASE='he0000;
 reg clk=0,reset=1,run=0;always #5 clk=~clk;
 wire read_clk;assign #2.75 read_clk=~clk;
 integer cycle=0,run_cycle=0,lines=0,line_sent=0,line_recv=0,line_start=0,max_line=0;
 integer pixel_sent=0,jwrite_sent=0,jread_sent=0,display_words=0,jread_words=0;
 integer contention_cycles=0;
 wire display_valid=run && lines>0 && line_sent<60;
 wire pixel_valid=run && pixel_sent<BACKGROUND_BURSTS;
 wire jwrite_valid=run && jwrite_sent<BACKGROUND_BURSTS;
 wire jread_valid=run && jread_sent<BACKGROUND_BURSTS;
 wire[23:0] display_addr=24'(DISPLAY_BASE+(lines-1)*480+line_sent*8);
 wire[23:0] pixel_addr=24'(PIXEL_BASE+pixel_sent*8);
 wire[23:0] jwrite_addr=24'(JWRITE_BASE+jwrite_sent*8+((MISALIGN_REQUEST!=0 && jwrite_sent==3)?1:0));
 wire[23:0] jread_addr=24'(JREAD_BASE+jread_sent*8);
 function automatic [15:0] word_value(input integer addr,input [15:0] salt);word_value=16'(addr)^salt;endfunction
 function automatic [127:0] block_value(input integer base,input [15:0] salt);
 integer i;begin for(i=0;i<8;i=i+1)block_value[i*16+:16]=word_value(base+i,salt);end endfunction
 wire[127:0] pixel_data=block_value(PIXEL_BASE+pixel_sent*8,16'h1357);
 wire[127:0] jwrite_data=block_value(JWRITE_BASE+jwrite_sent*8,16'h2468) ^ ((CORRUPT_PAYLOAD!=0 && jwrite_sent==50)?128'd1:128'd0);
 wire display_ready,pixel_ready,jwrite_ready,jread_ready,display_dvalid,jread_dvalid;
 wire[15:0] display_data,jread_data;wire req_valid,req_ready,req_write,rsp_valid,mem_idle,read_busy,protocol_fault;
 wire[23:0] req_addr;wire[127:0] req_data;wire[15:0] rsp_data;
 staging_arbiter arb(.clk(clk),.reset(reset),.display_valid(display_valid),.display_ready(display_ready),.display_addr(display_addr),
  .display_data_valid(display_dvalid),.display_data(display_data),.pixel_valid(pixel_valid),.pixel_ready(pixel_ready),.pixel_addr(pixel_addr),.pixel_data(pixel_data),
  .jwrite_valid(jwrite_valid),.jwrite_ready(jwrite_ready),.jwrite_addr(jwrite_addr),.jwrite_data(jwrite_data),
  .jread_valid(jread_valid),.jread_ready(jread_ready),.jread_addr(jread_addr),.jread_data_valid(jread_dvalid),.jread_data(jread_data),
  .request_valid(req_valid),.request_ready(req_ready),.request_write(req_write),.request_addr(req_addr),.request_data(req_data),
  .response_valid(rsp_valid),.response_data(rsp_data),.read_busy(read_busy),.protocol_fault(protocol_fault));
 wire[12:0] a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,ldqm,udqm;
 moonshine_sdram_burst #(.POWERUP_CYCLES(20),.REFRESH_CYCLES(750)) controller(
  .clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(req_valid),.request_ready(req_ready),
  .request_write(req_write),.request_address(req_addr),.request_burst_data(req_data),
  .response_valid(rsp_valid),.response_data(rsp_data),.idle(mem_idle),.sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),
  .sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(ldqm),.sdram_udqm(udqm));
 sdram_model_burst model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(ldqm),.udqm(udqm),.dq(dq));
 integer i;
 always @(posedge clk) begin
  cycle<=cycle+1;
  if(run)begin
   run_cycle<=run_cycle+1;
   if(protocol_fault)$fatal(1,"arbiter protocol fault");
   if(display_dvalid && jread_dvalid)$fatal(1,"response routed twice");
   if(display_valid && (pixel_valid || jwrite_valid || jread_valid))contention_cycles<=contention_cycles+1;
   if(display_valid && (pixel_ready || jwrite_ready || jread_ready))$fatal(1,"display priority violation");
   if(run_cycle%LINE_PERIOD==0 && lines<LINES)begin
    if(lines>0 && (line_sent!=60 || line_recv!=480))$fatal(1,"display line deadline line=%0d sent=%0d recv=%0d",lines-1,line_sent,line_recv);
    lines<=lines+1;line_sent<=0;line_recv<=0;line_start<=run_cycle;
   end
   if(lines==LINES && line_recv<480 && run_cycle-line_start>=LINE_PERIOD)$fatal(1,"final display line deadline recv=%0d",line_recv);
   if(display_ready)line_sent<=line_sent+1;
   if(pixel_ready)pixel_sent<=pixel_sent+1;
   if(jwrite_ready)jwrite_sent<=jwrite_sent+1;
   if(jread_ready)jread_sent<=jread_sent+1;
   if(display_dvalid)begin
    if(display_data!==word_value(DISPLAY_BASE+display_words,16'h55aa))$fatal(1,"display data index=%0d got=%h",display_words,display_data);
    display_words<=display_words+1;line_recv<=line_recv+1;
    if(line_recv==479 && run_cycle-line_start>max_line)max_line<=run_cycle-line_start;
   end
   if(jread_dvalid)begin
    if(jread_data!==word_value(JREAD_BASE+jread_words,16'ha55a))$fatal(1,"compressed read data index=%0d got=%h",jread_words,jread_data);
    jread_words<=jread_words+1;
   end
  end
 end
 initial begin
  for(i=0;i<LINES*480;i=i+1)model.mem[DISPLAY_BASE+i]=word_value(DISPLAY_BASE+i,16'h55aa);
  for(i=0;i<BACKGROUND_BURSTS*8;i=i+1)begin
   model.mem[JREAD_BASE+i]=word_value(JREAD_BASE+i,16'ha55a);
   model.mem[PIXEL_BASE+i]=16'hdead;model.mem[JWRITE_BASE+i]=16'hbeef;
  end
  model.mem[PIXEL_BASE-1]=16'habcd;model.mem[PIXEL_BASE+BACKGROUND_BURSTS*8]=16'hdcba;
  model.mem[JWRITE_BASE-1]=16'h789a;model.mem[JWRITE_BASE+BACKGROUND_BURSTS*8]=16'h987a;
  repeat(5)@(negedge clk);reset=0;
  while(!req_ready)@(negedge clk);
  @(negedge clk);run=1;
  while(lines<LINES || line_recv<480 || pixel_sent<BACKGROUND_BURSTS || jwrite_sent<BACKGROUND_BURSTS || jread_words<BACKGROUND_BURSTS*8)@(negedge clk);
  while(!mem_idle || read_busy)@(negedge clk);
  repeat(5)@(negedge clk);
  if(line_sent!=60||display_words!=LINES*480||jread_words!=BACKGROUND_BURSTS*8)$fatal(1,"missing output words");
  if(model.refreshes<10)$fatal(1,"insufficient refresh events %0d",model.refreshes);
  if(contention_cycles==0 || model.writes!=BACKGROUND_BURSTS*16 || model.write_bursts!=BACKGROUND_BURSTS*2)$fatal(1,"missing contention or write commands");
  for(i=0;i<BACKGROUND_BURSTS*8;i=i+1)begin
   if(model.mem[PIXEL_BASE+i]!==word_value(PIXEL_BASE+i,16'h1357))$fatal(1,"pixel write mismatch %0d",i);
   if(model.mem[JWRITE_BASE+i]!==word_value(JWRITE_BASE+i,16'h2468))$fatal(1,"compressed write mismatch %0d",i);
  end
  if(model.mem[PIXEL_BASE-1]!==16'habcd||model.mem[PIXEL_BASE+BACKGROUND_BURSTS*8]!==16'hdcba||
     model.mem[JWRITE_BASE-1]!==16'h789a||model.mem[JWRITE_BASE+BACKGROUND_BURSTS*8]!==16'h987a)$fatal(1,"write guard overwritten");
  $display("STAGING_ARBITER_PASS lines=%0d display_words=%0d max_line_cycles=%0d period_cycles=%0d pixel=%0d jwrite=%0d jread=%0d refreshes=%0d contention_cycles=%0d",LINES,display_words,max_line,LINE_PERIOD,pixel_sent,jwrite_sent,jread_sent,model.refreshes,contention_cycles);$finish;
 end
 initial begin #2000000;$fatal(1,"watchdog");end
endmodule
