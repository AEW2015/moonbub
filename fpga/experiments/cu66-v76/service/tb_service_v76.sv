`timescale 1ns/1ps
module tb_service_v76 #(parameter real TAC_NS=2.0,FLIGHT_NS=4.0);
 logic clk=0,read_clk=0,rst=1,abort_i=0,aux_abort_i=0;
 always #5 clk=~clk;
 always @(clk)read_clk<=#2.75 ~clk;
 logic read_valid=0,read_ready;logic [63:0] read_generation=0;logic [1:0] read_bank=0,read_plane=0;logic [16:0]read_index=0;
 logic read_rsp_valid,read_rsp_ready=0;logic [63:0]read_rsp_generation;logic[1:0]read_rsp_bank,read_rsp_plane;logic[16:0]read_rsp_index;logic[511:0]read_rsp_pixels;logic read_rsp_error;
 logic write_valid=0,write_ready;logic[63:0]write_generation=0;logic[1:0]write_bank=0,write_plane=0;logic[16:0]write_index=0;logic[511:0]write_pixels=0;
 logic write_done_valid,write_done_ready=0;logic[63:0]write_done_generation;logic[1:0]write_done_bank,write_done_plane;logic[16:0]write_done_index;logic write_done_error;
 logic tile_busy,tile_aborted;
 logic aux_req_valid=0,aux_req_ready,aux_req_write=0;logic[23:0]aux_req_addr=0;logic[15:0]aux_req_data=0;
 logic aux_req_read_burst=0;logic[127:0]aux_rsp_burst_data;
 logic aux_req_burst=0;logic [127:0]aux_req_burst_data=0;logic [15:0]aux_req_byte_enable=0;
 logic aux_rsp_valid,aux_rsp_ready=0;logic[15:0]aux_rsp_data;logic aux_rsp_error,aux_busy,aux_aborted;
 wire[12:0]sdram_a;wire[1:0]sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;logic idle;
 logic[31:0]cache_hits,cache_misses,completed_reads,completed_writes;
 logic[31:0]p0_cache_hits,p0_cache_misses,p0_row_reads,p0_wait_cycles,p0_service_cycles,p1_cache_hits,p1_cache_misses,p0_read_wait_cycles,p0_read_service_cycles;
 logic lcd_req_valid=0,lcd_req_ready;logic[23:0]lcd_req_addr=0;
 logic lcd_rsp_valid,lcd_rsp_ready=0,lcd_rsp_last,lcd_rsp_error,lcd_busy;logic[15:0]lcd_rsp_data;
 cu74_memory_system #(.POWERUP_CYCLES(20)) dut(.*);
 cu72_sdram_model #(.T_AC_NS(TAC_NS),.CLOCK_FLIGHT_NS(FLIGHT_NS)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 integer cycles=0,checks=0;always @(posedge clk)cycles<=cycles+1;
 initial begin #300000000;$fatal(1,"service watchdog");end
 function automatic logic[15:0] sample(input integer addr);
  sample=16'((addr*37)^(addr>>5)^32'h5ac3);
 endfunction
 function automatic integer plane_off(input integer p);
  plane_off=p==0?0:p==1?172800:216000;
 endfunction
 task automatic write_block(input integer addr);
  begin
   @(negedge clk);aux_req_valid=1;aux_req_write=1;aux_req_read_burst=0;aux_req_burst=1;aux_req_addr=24'(addr);aux_req_byte_enable=16'hffff;
   for(integer i=0;i<8;i=i+1)aux_req_burst_data[i*16+:16]=sample(addr+i);
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;
   while(!aux_rsp_valid)@(negedge clk);
   if(aux_rsp_error)$fatal(1,"setup write error");
   aux_rsp_ready=1;@(posedge clk);@(negedge clk);aux_rsp_ready=0;
  end
 endtask
 task automatic read_block(input integer addr,input integer route);
  begin
   if(issue_gap!=0)@(negedge clk);
   if(route==0)begin
    aux_req_valid=1;aux_req_write=0;aux_req_read_burst=1;aux_req_burst=0;aux_req_byte_enable=0;aux_req_addr=24'(addr);
    do @(posedge clk);while(!aux_req_ready);
    first_accept=cycles;if(last_drain>=0)begin if(cycles-last_drain<gap_min)gap_min=cycles-last_drain;if(cycles-last_drain>gap_max)gap_max=cycles-last_drain;end
    @(negedge clk);aux_req_valid=0;
    while(!aux_rsp_valid)@(negedge clk);
    if(aux_rsp_error)$fatal(1,"foreground P1 error");
    for(integer i=0;i<8;i=i+1)begin if(aux_rsp_burst_data[i*16+:16]!==sample(addr+i))$fatal(1,"P1 data addr%h word%0d",addr,i);checks=checks+1;end
    if(aux_rsp_data!==sample(addr))$fatal(1,"P1 scalar snapshot mismatch");
    aux_rsp_ready=1;@(posedge clk);last_drain=cycles;@(negedge clk);aux_rsp_ready=0;
   end else begin
    lcd_req_valid=1;lcd_req_addr=24'(addr);
    do @(posedge clk);while(!lcd_req_ready);
    first_accept=cycles;if(last_drain>=0)begin if(cycles-last_drain<gap_min)gap_min=cycles-last_drain;if(cycles-last_drain>gap_max)gap_max=cycles-last_drain;end
    @(negedge clk);lcd_req_valid=0;
    for(integer i=0;i<8;i=i+1)begin
     while(!lcd_rsp_valid)@(negedge clk);
     if(lcd_rsp_error||lcd_rsp_last!==(i==7)||lcd_rsp_data!==sample(addr+i))$fatal(1,"LCD data/framing addr%h word%0d",addr,i);
     if(!lcd_busy)$fatal(1,"LCD no busy during response");
     checks=checks+1;lcd_rsp_ready=1;@(posedge clk);if(i==7)last_drain=cycles;@(negedge clk);lcd_rsp_ready=0;
    end
   end
  end
 endtask
 logic[31:0]trace[0:35039];logic[31:0]refs[0:7805];
 integer route=0,bg_mode=0,measure_start=0,reference_bank=0,issue_gap=0;logic run_bg=0,finished=0;
 integer released_w=0,released_r=0,done_w=0,done_r=0,bg_read_words=0,bg_late_w=0,bg_late_r=0;
 always @(posedge clk)begin
  if(run_bg&&bg_mode==1)begin
   while((64'(cycles)-64'(measure_start))*64'd243000>=(64'(released_w)+64'd1)*64'd100000000)released_w=released_w+1;
   while((64'(cycles)-64'(measure_start))*64'd234180>=(64'(released_r)+64'd1)*64'd100000000)released_r=released_r+1;
  end
 end
 task automatic background;
  integer turn,t,p,idx,addr,job;
  begin
   turn=0;
   while(run_bg||done_w<released_w||done_r<released_r)begin
    @(negedge clk);
    if(bg_mode==2&&run_bg)begin
     if(turn==0)released_w=done_w+1;else released_r=done_r+1;
    end
    if(done_w<released_w&&(done_r>=released_r||turn==0))begin
     job=done_w;t=done_w%8100;p=t<5400?0:t<6750?1:2;idx=p==0?t:p==1?t-5400:t-6750;
     addr=32'h480000+plane_off(p)+idx*32;
     write_generation=2;write_bank=1;write_plane=2'(p);write_index=17'(idx);
     for(integer i=0;i<32;i=i+1)write_pixels[i*16+:16]=sample(addr+i);
     write_valid=1;do @(posedge clk);while(!write_ready);@(negedge clk);write_valid=0;
     while(!write_done_valid)@(negedge clk);
     if(write_done_error||write_done_generation!=2||write_done_bank!=1||write_done_plane!=2'(p)||write_done_index!=17'(idx))$fatal(1,"background write identity/error");
     write_done_ready=1;@(posedge clk);@(negedge clk);write_done_ready=0;done_w=done_w+1;turn=1;
     if(bg_mode==1&&(64'(cycles)-64'(measure_start))*30>(64'(job)/64'd8100+64'd1)*100000000)bg_late_w=bg_late_w+1;
    end else if(done_r<released_r)begin
     job=done_r;t=int'(refs[done_r%7806]);p=t>>17;idx=t&131071;addr=(reference_bank==0?32'h080000:32'h880000)+plane_off(p)+idx*32;
     read_generation=3;read_bank=2'(reference_bank);read_plane=2'(p);read_index=17'(idx);read_valid=1;
     do @(posedge clk);while(!read_ready);@(negedge clk);read_valid=0;
     while(!read_rsp_valid)@(negedge clk);
     if(read_rsp_error||read_rsp_generation!=3||read_rsp_bank!=2'(reference_bank)||read_rsp_plane!=2'(p)||read_rsp_index!=17'(idx))$fatal(1,"background read identity/error");
     for(integer i=0;i<32;i=i+1)begin if(read_rsp_pixels[i*16+:16]!==sample(addr+i))$fatal(1,"background read data");bg_read_words=bg_read_words+1;end
     read_rsp_ready=1;@(posedge clk);@(negedge clk);read_rsp_ready=0;done_r=done_r+1;turn=0;
     if(bg_mode==1&&(64'(cycles)-64'(measure_start))*30>(64'(job)/64'd7806+64'd1)*100000000)bg_late_r=bg_late_r+1;
    end
   end
  end
 endtask
 integer gap_min=1000000,gap_max=0,last_drain=-1,first_accept=-1;
 integer ptr,s,first,last,release_cycle,deadline_cycle,start_cycle,elapsed,max_service=0,min_service=1000000,misses=0,max_lateness=0;
 integer rd0,wr0,act0,pre0,ref0,wcmd0,wbeat0,trace_count,end_cycle,end_done_w,end_done_r,end_released_w,end_released_r;
 string tracefile,reffile;
 initial begin
  if(!$value$plusargs("TRACE=%s",tracefile))$fatal(1,"trace path missing");
  if(!$value$plusargs("REF=%s",reffile))$fatal(1,"reference trace missing");
  if(!$value$plusargs("ROUTE=%d",route))route=0;
  if(!$value$plusargs("BACKGROUND=%d",bg_mode))bg_mode=0;
  if(!$value$plusargs("REFBANK=%d",reference_bank))reference_bank=0;
  if(!$value$plusargs("ISSUE_GAP=%d",issue_gap))issue_gap=0;
  if(route<0||route>1||bg_mode<0||bg_mode>2||(reference_bank!=0&&reference_bank!=2)||issue_gap<0||issue_gap>1)$fatal(1,"invalid test mode");
  $readmemh(tracefile,trace);$readmemh(reffile,refs);
  repeat(8)@(negedge clk);rst=0;while(!idle)@(negedge clk);
  // Every measured source word is initialized through physical request/command writes.
  for(integer a=0;a<259200;a=a+8)write_block(32'h080000+a);
  for(integer a=0;a<21120;a=a+8)write_block(32'h100000+a);
  for(integer a=0;a<259200;a=a+8)write_block(32'h880000+a);
  if(model.writes!=539520||model.write_commands!=67440||model.write_bus_beats!=539520)$fatal(1,"setup actual fullwrite counts");
  if(tile_aborted||aux_aborted||tile_busy||aux_busy)$fatal(1,"setup not drained");
  measure_start=cycles;rd0=model.reads;wr0=model.writes;act0=model.acts;pre0=model.pres;ref0=model.refreshes;wcmd0=model.write_commands;wbeat0=model.write_bus_beats;run_bg=bg_mode!=0;
  fork
   background();
   begin
    ptr=0;
    for(s=0;s<90;s=s+1)begin
     release_cycle=measure_start+integer'((64'(s)*147403024)/10000);
     deadline_cycle=measure_start+integer'(((64'(s)+64'd1)*147403024)/10000);
     while(cycles<release_cycle)@(negedge clk);
     start_cycle=cycles;first=ptr;last_drain=-1;
     while(ptr<35040&&trace[ptr][31:24]==8'(s))begin read_block(int'({8'd0,trace[ptr][23:0]}),route);ptr=ptr+1;end
     last=cycles;elapsed=last-start_cycle;trace_count=ptr-first;
     if(elapsed>max_service)max_service=elapsed;if(elapsed<min_service)min_service=elapsed;
     if(last>deadline_cycle)begin misses=misses+1;if(last-deadline_cycle>max_lateness)max_lateness=last-deadline_cycle;end
     $display("SERVICE_STRIP strip=%0d release_cycle=%0d start_cycle=%0d end_cycle=%0d deadline_cycle=%0d service_cycles=%0d wait_cycles=%0d bursts=%0d late_cycles=%0d",s,release_cycle,start_cycle,last,deadline_cycle,elapsed,start_cycle-release_cycle,trace_count,last>deadline_cycle?last-deadline_cycle:0);
    end
    if(ptr!=35040)$fatal(1,"incomplete trace");end_cycle=cycles;end_done_w=done_w;end_done_r=done_r;end_released_w=released_w;end_released_r=released_r;run_bg=0;finished=1;
   end
  join
  if(!finished||done_w!=released_w||done_r!=released_r||read_valid||write_valid||tile_busy||aux_busy||lcd_busy)$fatal(1,"background not drained");
  if(tile_aborted||aux_aborted||checks!=280320)$fatal(1,"functional completion counts");
  if(cache_hits!=p0_cache_hits+p1_cache_hits||cache_misses!=p0_cache_misses+p1_cache_misses||p0_row_reads!=4*done_r)$fatal(1,"profile accounting");
  if(completed_reads!=32'(model.reads)||completed_writes!=32'(model.write_commands)||p0_wait_cycles<p0_read_wait_cycles||p0_service_cycles<p0_read_service_cycles)$fatal(1,"completed/profile subset counts");
  if(model.mem[model.last_write_address]!==model.last_write_data)$fatal(1,"last physical write trace");
  $display("SERVICE_PASS route=%0d background=%0d reference_bank=%0d issue_gap=%0d min_drain_to_accept=%0d max_drain_to_accept=%0d first_accept_cycle=%0d strips=90 bursts=35040 compared_words=%0d measured_cycles=%0d min_service_cycles=%0d max_service_cycles=%0d deadline_misses=%0d max_lateness_cycles=%0d released_w=%0d released_r=%0d complete_w_at_end=%0d complete_r_at_end=%0d drained_w=%0d drained_r=%0d background_read_words=%0d late_bg_w=%0d late_bg_r=%0d reads=%0d writes=%0d write_commands=%0d write_bus_beats=%0d ACT=%0d PRE=%0d REF=%0d cache_hits=%0d cache_misses=%0d p0_read_wait=%0d p0_read_service=%0d",route,bg_mode,reference_bank,issue_gap,gap_min,gap_max,first_accept,checks,end_cycle-measure_start,min_service,max_service,misses,max_lateness,end_released_w,end_released_r,end_done_w,end_done_r,done_w,done_r,bg_read_words,bg_late_w,bg_late_r,model.reads-rd0,model.writes-wr0,model.write_commands-wcmd0,model.write_bus_beats-wbeat0,model.acts-act0,model.pres-pre0,model.refreshes-ref0,cache_hits,cache_misses,p0_read_wait_cycles,p0_read_service_cycles);
  $finish;
 end
endmodule
