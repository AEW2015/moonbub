`timescale 1ns/1ps
module tb_memory;
 logic clk=0,read_clk=0,rst=1,abort_i=0,aux_abort_i=0;
 always #5 clk=~clk;
 always @(clk)read_clk<=#2.625 ~clk;
 logic read_valid=0,read_ready;logic [63:0] read_generation=0;logic [1:0] read_bank=0,read_plane=0;logic [16:0]read_index=0;
 logic read_rsp_valid,read_rsp_ready=0;logic [63:0]read_rsp_generation;logic[1:0]read_rsp_bank,read_rsp_plane;logic[16:0]read_rsp_index;logic[511:0]read_rsp_pixels;logic read_rsp_error;
 logic write_valid=0,write_ready;logic[63:0]write_generation=0;logic[1:0]write_bank=0,write_plane=0;logic[16:0]write_index=0;logic[511:0]write_pixels=0;
 logic write_done_valid,write_done_ready=0;logic[63:0]write_done_generation;logic[1:0]write_done_bank,write_done_plane;logic[16:0]write_done_index;logic write_done_error;
 logic tile_busy,tile_aborted;
 logic aux_req_valid=0,aux_req_ready,aux_req_write=0;logic[23:0]aux_req_addr=0;logic[15:0]aux_req_data=0;
 logic aux_rsp_valid,aux_rsp_ready=0;logic[15:0]aux_rsp_data;logic aux_rsp_error,aux_busy,aux_aborted;
 wire[12:0]sdram_a;wire[1:0]sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;logic idle;
 logic lcd_req_valid=0,lcd_req_ready,lcd_rsp_valid,lcd_rsp_ready=0,lcd_rsp_error,lcd_abort_i=0,lcd_busy,lcd_aborted;
 logic[23:0]lcd_req_addr=0;logic[127:0]lcd_rsp_data;logic[31:0]lcd_completed_reads,lcd_max_wait;
 logic rgb_req_valid=0,rgb_req_ready,rgb_rsp_valid,rgb_rsp_ready=1,rgb_rsp_error,rgb_abort_i=0,rgb_busy,rgb_aborted;
 logic[23:0]rgb_req_addr=0;logic[127:0]rgb_req_data=0;logic[15:0]rgb_req_mask=16'hffff;
 logic[31:0]rgb_completed_writes,rgb_max_wait;
 logic[31:0]cache_hits,cache_misses,completed_reads,completed_writes;
 cu71_memory_system_direct #(.POWERUP_CYCLES(20)) dut(.*);
 sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS(8.489),.CLOCK_FLIGHT_NS(3.768),.T_OH_NS(2.223)) model(.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 `include "cu70_memory_map.svh"
 integer pin_read_beats=0;
 always @(posedge clk)if(!rst&&dut.mem_rsp_valid)pin_read_beats=pin_read_beats+1;
 integer observed_LCD=0,observed_BG=0;
 always @(posedge clk)if(!rst&&dut.mem_req_valid&&dut.mem_req_ready)begin
  if(dut.bridge.owner==2)observed_LCD=observed_LCD+1;else observed_BG=observed_BG+1;
 end
 integer checks=0,tiles=0,aux_ops=0,aborts=0,cycles=0;
 integer seed=7001,seed_input,max_aux_wait=0;
 logic[511:0]pattern;
 logic[15:0]got;
 integer b,p,t,j,k,idx,base,pitch,by,bx,address0,prior_writes,prior_refreshes;
 always @(posedge clk)cycles=cycles+1;
 function automatic logic[511:0]make_pattern(input integer salt);
  for(integer i=0;i<64;i=i+1)make_pattern[8*i+:8]=8'((salt*37+i*19)^(i/8));
 endfunction
 task automatic aux(input bit writing,input logic[23:0]address,input logic[15:0]data,input bit expect_bad,output logic[15:0]result);
  logic[15:0]saved;integer wait_count;
  begin
   @(negedge clk);aux_req_valid=1;aux_req_write=writing;aux_req_addr=address;aux_req_data=data;
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;wait_count=0;
   while(!aux_rsp_valid)begin @(negedge clk);wait_count=wait_count+1;if(wait_count>2000)$fatal(1,"aux watchdog address%h",address);end
   if(wait_count>max_aux_wait)max_aux_wait=wait_count;
   if(aux_rsp_error!==expect_bad)$fatal(1,"aux error address%h got%b expected%b",address,aux_rsp_error,expect_bad);
   saved=aux_rsp_data;
   repeat(2)begin @(negedge clk);if(!aux_rsp_valid||aux_rsp_data!==saved||aux_rsp_error!==expect_bad)$fatal(1,"aux held response changed");end
   result=saved;aux_rsp_ready=1;@(posedge clk);@(negedge clk);aux_rsp_ready=0;aux_ops=aux_ops+1;checks=checks+1;
  end
 endtask
 task automatic write_tile(input integer bank_id,plane_id,tile_id,input logic[511:0]pixels,input bit expect_bad);
  begin
   if(bank_id<0||bank_id>3||plane_id<0||plane_id>3||tile_id<0||tile_id>131071)$fatal(1,"write taskportdomain");
   @(negedge clk);write_valid=1;write_generation=64'd100+64'(tiles);write_bank=2'(bank_id);write_plane=2'(plane_id);write_index=17'(tile_id);write_pixels=pixels;
   do @(posedge clk);while(!write_ready);
   @(negedge clk);write_valid=0;
   while(!write_done_valid)@(negedge clk);
   if(write_done_generation!=write_generation||write_done_bank!=write_bank||write_done_plane!=write_plane||write_done_index!=write_index||write_done_error!==expect_bad)$fatal(1,"write identity/error");
   repeat(3)begin @(negedge clk);if(!write_done_valid||write_done_error!==expect_bad)$fatal(1,"write result changed");end
   write_done_ready=1;@(posedge clk);@(negedge clk);write_done_ready=0;tiles=tiles+1;checks=checks+1;
  end
 endtask
 task automatic read_tile(input integer bank_id,plane_id,tile_id,input logic[511:0]pixels,input bit expect_bad);
  logic[511:0]saved;
  begin
   if(bank_id<0||bank_id>3||plane_id<0||plane_id>3||tile_id<0||tile_id>131071)$fatal(1,"read taskportdomain");
   @(negedge clk);read_valid=1;read_generation=64'd200+64'(tiles);read_bank=2'(bank_id);read_plane=2'(plane_id);read_index=17'(tile_id);
   do @(posedge clk);while(!read_ready);
   @(negedge clk);read_valid=0;
   while(!read_rsp_valid)@(negedge clk);
   if(read_rsp_generation!=read_generation||read_rsp_bank!=read_bank||read_rsp_plane!=read_plane||read_rsp_index!=read_index||read_rsp_error!==expect_bad)$fatal(1,"read identity/error");
   if(!expect_bad&&read_rsp_pixels!==pixels)$fatal(1,"tile mismatch bank%0d plane%0d index%0d got%h expected%h",bank_id,plane_id,tile_id,read_rsp_pixels,pixels);
   saved=read_rsp_pixels;
   repeat(3)begin @(negedge clk);if(!read_rsp_valid||read_rsp_pixels!==saved)$fatal(1,"read response changed");end
   read_rsp_ready=1;@(posedge clk);@(negedge clk);read_rsp_ready=0;tiles=tiles+1;checks=checks+1;
  end
 endtask
 task automatic abort_write(input integer accepted_words);
  integer before_count,initial_writes;
  begin
   initial_writes=model.writes;
   @(negedge clk);write_valid=1;write_generation=700;write_bank=0;write_plane=0;write_index=100;write_pixels=make_pattern(accepted_words+900);
   do @(posedge clk);while(!write_ready);
   @(negedge clk);write_valid=0;while(model.writes-initial_writes<accepted_words)@(negedge clk);
   before_count=model.writes;abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(write_done_valid||read_rsp_valid)$fatal(1,"aborted tile exposed success");@(negedge clk);end
   if(!tile_aborted)$fatal(1,"missing tileabort completion");
   if(model.writes-before_count>1)$fatal(1,"abort started new writes");
   // Previously accepted controller write may have reached the array, but all
   // later writes are canceled and the transaction never reports success.
   aborts=aborts+1;checks=checks+1;
  end
 endtask
 task automatic abort_read(input integer accepted_bursts);
  integer initial_reads;
  begin
   initial_reads=model.reads;
   @(negedge clk);read_valid=1;read_generation=800;read_bank=2;read_plane=2;read_index=17'(200+accepted_bursts*7);
   do @(posedge clk);while(!read_ready);
   @(negedge clk);read_valid=0;
   while(model.reads-initial_reads<accepted_bursts)@(negedge clk);
   abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(read_rsp_valid||write_done_valid)$fatal(1,"abortedreadexposedsuccess");@(negedge clk);end
   if(!tile_aborted)$fatal(1,"missingreadabortcompletion");
   aborts=aborts+1;checks=checks+1;
  end
 endtask
 initial begin
  if($value$plusargs("SEED=%d",seed_input))seed=seed_input;
  // Guard sentinels live outside the public allocation ranges.
  model.mem[CANONICAL0_BASE-1]=16'hcafe;model.mem[24'(CANONICAL0_BASE+CANONICAL0_WORDS)]=16'hbabe;
  repeat(5)@(negedge clk);rst=0;while(!idle)@(negedge clk);
  // Highest physical word, four internal bank positions and exact boundaries.
  for(b=0;b<4;b=b+1)begin
   address0=b==0?int'(CANONICAL0_BASE):b==1?int'(CANONICAL1_BASE):b==2?int'(CANONICAL2_BASE):int'(DIAGNOSTIC_BASE);
   aux(1,24'(address0),16'(32'h1234+b),0,got);aux(0,24'(address0),0,0,got);if(got!==16'(32'h1234+b))$fatal(1,"bank/address alias");
  end
  aux(1,24'hffffff,16'hfedc,0,got);aux(0,24'hffffff,0,0,got);if(got!==16'hfedc)$fatal(1,"top physical word");
  prior_writes=model.writes;
  aux(1,CANONICAL0_BASE-1,16'h0000,1,got);aux(0,CANONICAL0_BASE+24'(CANONICAL0_WORDS),0,1,got);
  aux(0,24'h000000,0,1,got);if(model.writes!=prior_writes)$fatal(1,"invalid write reachedSDRAM");
  // Sequential cache hits and alias invalidation by the other client.
  for(j=0;j<16;j=j+1)aux(1,DIAGNOSTIC_BASE+24'(j),16'(j*77),0,got);
  for(j=0;j<16;j=j+1)begin aux(0,DIAGNOSTIC_BASE+24'(j),0,0,got);if(got!==16'(j*77))$fatal(1,"cached sequence");end
  // Each plane/bank includes first,last, row/page crossing and seeded tile IDs.
  for(b=0;b<3;b=b+1)for(p=0;p<3;p=p+1)for(t=0;t<12;t=t+1)begin
   idx=t==0?0:t==1?(p==0?5399:1349):t==2?(p==0?89:44):t==3?(p==0?90:45):t==4?127:t==5?128:(t*131+b*67+p*83+seed)% (p==0?5400:1350);
   pattern=make_pattern(b*1000+p*100+idx);write_tile(b,p,idx,pattern,0);read_tile(b,p,idx,pattern,0);
   // Independent scalar physical-address readback defeats symmetric tile-map bugs.
   base=int'(canonical_base(2'(b)))+(p==0?0:p==1?172800:216000);pitch=p==0?360:180;by=idx/(p==0?90:45);bx=idx%(p==0?90:45);
   for(j=0;j<32;j=j+1)begin
    address0=base+idx*32+j;if(address0<0||address0>=16777216)$fatal(1,"scalaroracleaddress");aux(0,24'(address0),0,0,got);
    if(got!==pattern[16*j+:16])$fatal(1,"scalar layout mismatch");
   end
  end
  pattern=make_pattern(555);write_tile(0,0,0,pattern,0);aux(0,CANONICAL0_BASE,0,0,got);
  pattern[15:0]=16'h4321;write_tile(0,0,0,pattern,0);aux(0,CANONICAL0_BASE,0,0,got);if(got!==16'h4321)$fatal(1,"cross-client cache stale");read_tile(0,0,0,pattern,0);
  prior_writes=model.writes;
  write_tile(3,0,0,0,1);write_tile(0,3,0,0,1);write_tile(0,0,5400,0,1);read_tile(0,1,1350,0,1);
  if(model.writes!=prior_writes)$fatal(1,"invalid tile reachedSDRAM");
  // Legacy single-write abort task not applicable to masked BL8; new cases below.
  for(k=1;k<=4;k=k+1)abort_read(k);
  pattern=make_pattern(777);write_tile(2,2,1349,pattern,0);read_tile(2,2,1349,pattern,0);
  // Actual simultaneous canonical and auxiliary clients share command service.
  // This stresses RR ownership and per-client cache tags, not a reserved-slot model.
  fork
   begin
    write_tile(1,1,500,make_pattern(991),0);
   end
   begin : parallel_aux
    integer n;logic[15:0]value;
    for(n=0;n<96;n=n+1)begin
     aux(1,HUD2_BASE+24'(n),16'(n*191+7),0,value);
     aux(0,HUD2_BASE+24'(n),0,0,value);
     if(value!==16'(n*191+7))$fatal(1,"concurrentauxdata");
    end
   end
  join
  read_tile(1,1,500,make_pattern(991),0);
  // Aux accepted controller read and write drain paths.
  for(k=0;k<2;k=k+1)begin
   @(negedge clk);aux_req_valid=1;aux_req_write=1'(k);aux_req_addr=DIAGNOSTIC_BASE+24'd32;aux_req_data=16'habcd;
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;repeat(4)@(negedge clk);aux_abort_i=1;@(posedge clk);@(negedge clk);aux_abort_i=0;
   while(aux_busy)begin if(aux_rsp_valid)$fatal(1,"aborted aux response");@(negedge clk);end
   if(!aux_aborted)$fatal(1,"missingauxabortcompletion");
   aborts=aborts+1;
  end
  // Held auxiliary response must not prevent dedicated LCD or tile service.
  for(j=0;j<8;j=j+1)aux(1,RGB0_BASE+24'(j),16'(16'h6000+j),0,got);
  @(negedge clk);aux_req_valid=1;aux_req_write=0;aux_req_addr=DIAGNOSTIC_BASE;
  do @(posedge clk);while(!aux_req_ready);
  @(negedge clk);aux_req_valid=0;while(!aux_rsp_valid)@(negedge clk);
  @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE;
  do @(posedge clk);while(!lcd_req_ready);
  @(negedge clk);lcd_req_valid=0;
  begin: held_aux integer wait_lcd;wait_lcd=0;
   while(!lcd_rsp_valid)begin @(negedge clk);wait_lcd=wait_lcd+1;if(wait_lcd>200)$fatal(1,"stalled aux blocked LCD");end
   for(integer n=0;n<8;n=n+1)if(lcd_rsp_data[n*16+:16]!==16'(16'h6000+n))$fatal(1,"LCD BL8 ordering");
   if(lcd_rsp_error||!aux_rsp_valid)$fatal(1,"independent responses");
   repeat(5)@(negedge clk);
   lcd_rsp_ready=1;aux_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;aux_rsp_ready=0;checks=checks+1;
  end
  // A held LCD response must not prevent another auxiliary write from draining.
  @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE;
  do @(posedge clk);while(!lcd_req_ready);
  @(negedge clk);lcd_req_valid=0;while(!lcd_rsp_valid)@(negedge clk);
  aux(1,DIAGNOSTIC_BASE+24'd128,16'h7bad,0,got);
  if(!lcd_rsp_valid||lcd_rsp_data[15:0]!==16'h6000)$fatal(1,"held LCD response changed");
  lcd_abort_i=1;@(posedge clk);@(negedge clk);lcd_abort_i=0;
  while(lcd_busy)@(negedge clk);
  if(!lcd_aborted||lcd_rsp_valid)$fatal(1,"LCD abort did not drain held response");checks=checks+1;
  // Reject unaligned LCD request without issuing any controller READ.
  prior_writes=model.reads;
  lcd_req_valid=1;lcd_req_addr=RGB0_BASE+1;
  do @(posedge clk);while(!lcd_req_ready);
  @(negedge clk);lcd_req_valid=0;while(!lcd_rsp_valid)@(negedge clk);
  if(!lcd_rsp_error||model.reads!=prior_writes)$fatal(1,"LCD alignment guard");
  lcd_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;checks=checks+1;
  // Abort during each of the8accepted physical write beats. The accepted row
  // drains normally, candidate is not published, no new row starts afterwards.
  for(k=1;k<=8;k=k+1)begin
   prior_writes=model.writes;
   write_valid=1;write_generation=900+k;write_bank=0;write_plane=0;write_index=100;write_pixels=make_pattern(k);
   do @(posedge clk);while(!write_ready);
   @(negedge clk);write_valid=0;
   while(model.writes-prior_writes<k)@(negedge clk);
   abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(write_done_valid)$fatal(1,"accepted row abort exposed success");@(negedge clk);end
   if(!tile_aborted||model.writes-prior_writes!=8)$fatal(1,"accepted row abort failed drain");
   checks=checks+1;aborts=aborts+1;
  end
  // LCD abort after each accepted read-data beat: no success is exposed,
  // but all8controllerbeats finish before the client allocation is released.
  for(k=0;k<8;k=k+1)begin
   @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE;
   do @(posedge clk);while(!lcd_req_ready);
   @(negedge clk);lcd_req_valid=0;
   while(!(dut.bridge.state==2&&dut.bridge.beat==k&&dut.mem_rsp_valid))@(negedge clk);
   lcd_abort_i=1;@(posedge clk);@(negedge clk);lcd_abort_i=0;
   while(lcd_busy)begin if(lcd_rsp_valid)$fatal(1,"aborted LCD exposed successful response");@(negedge clk);end
   if(!lcd_aborted)$fatal(1,"missing accepted LCD abort drain");checks=checks+1;aborts=aborts+1;
  end
  // Auxiliary masked write abort at everyphysicalbeat; completion is drained,
  // never canceled at request-queue acceptance or acknowledged as success.
  for(k=1;k<=8;k=k+1)begin
   prior_writes=model.writes;
   aux_req_valid=1;aux_req_write=1;aux_req_addr=DIAGNOSTIC_BASE+24'd80;aux_req_data=16'h7dab;
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;
   while(model.writes-prior_writes<k)@(negedge clk);
   aux_abort_i=1;@(posedge clk);@(negedge clk);aux_abort_i=0;
   while(aux_busy)begin if(aux_rsp_valid)$fatal(1,"aborted aux exposed successful response");@(negedge clk);end
   if(!aux_aborted||model.writes-prior_writes!=8)$fatal(1,"accepted aux write failed drain");checks=checks+1;aborts=aborts+1;
  end
  // A full480word line under concurrentcanonical+HUD work. This measures,
  // rather than assumes, the line deadline;8cycle gaps mimic current serializer.
  for(j=0;j<480;j=j+1)aux(1,RGB0_BASE+24'(j),16'(16'h6000+j),0,got);
  fork
   begin: lcd_line_measure
    integer start_cycle,n,m;logic[127:0]held;start_cycle=cycles;
    for(n=0;n<60;n=n+1)begin
     @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE+24'(n*8);
     do @(posedge clk);while(!lcd_req_ready);
     @(negedge clk);lcd_req_valid=0;
     while(!lcd_rsp_valid)@(negedge clk);
     if(lcd_rsp_error)$fatal(1,"concurrent LCD response error");
     for(m=0;m<8;m=m+1)if(lcd_rsp_data[m*16+:16]!==16'(16'h6000+n*8+m))$fatal(1,"concurrent LCD data mismatch");
     held=lcd_rsp_data;
     repeat(2)begin @(negedge clk);if(!lcd_rsp_valid||lcd_rsp_data!==held)$fatal(1,"LCD held payload unstable");end
     lcd_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;
     repeat(8)@(negedge clk);
    end
    $display("CU71_LCD_LINE_MEASURE clocks=%0d words=480 max_backend_wait=%0d concurrent_tile_HUD=1 deadline_gate=NOT_QUALIFIED",cycles-start_cycle,lcd_max_wait);
   end
   begin: line_background_tile
    write_tile(1,0,230,make_pattern(600),0);
   end
   begin: line_background_hud
    integer n;logic[15:0]value;
    for(n=0;n<96;n=n+1)aux(1,HUD2_BASE+24'(n),16'(n*13+3),0,value);
   end
  join
  begin: direct_command_proof
   integer old_r,old_w,old_mask;logic[511:0]data;
   data=make_pattern(1777);old_w=completed_writes;old_mask=model.masked_bytes;
   write_tile(2,2,1349,data,0);
   if(completed_writes-old_w!=4||model.masked_bytes!=old_mask)$fatal(1,"directtilewriteisnot4fullBL8");
   old_r=completed_reads;read_tile(2,2,1349,data,0);
   if(completed_reads-old_r!=4)$fatal(1,"directtilereadisnot4fullBL8");
   for(integer n=0;n<32;n=n+1)begin
    aux(0,CANONICAL2_BASE+24'd216000+24'(1349*32+n),0,0,got);
    if(got!==data[n*16+:16])$fatal(1,"directlasttilelinearphysicaloracle");
   end
   $display("CU71_DIRECT_TILE_COMMAND_PASS full_read_BL8=4 full_write_BL8=4 physical_words=32 logical_bytes=64 masked_write_bytes=0");
  end
  // Every one of32physical write-beat abort positions, acrossall4bursts.
  for(k=1;k<=32;k=k+1)begin: write_abort_all
   logic[511:0]data;integer expected_beats;
   data=make_pattern(k+1900);prior_writes=model.writes;expected_beats=((k+7)/8)*8;
   @(negedge clk);write_valid=1;write_generation=1900+k;write_bank=1;write_plane=1;write_index=99;write_pixels=data;
   do @(posedge clk);while(!write_ready);
   @(negedge clk);write_valid=0;
   while(model.writes-prior_writes<k)@(negedge clk);
   abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(write_done_valid||read_rsp_valid)$fatal(1,"directwriteabortsuccessleak");@(negedge clk);end
   if(!tile_aborted||model.writes-prior_writes!=expected_beats)$fatal(1,"directwriteabortdraincount");
   for(integer n=0;n<expected_beats;n=n+1)begin
    aux(0,CANONICAL1_BASE+24'd172800+24'(99*32+n),0,0,got);
    if(got!==data[n*16+:16])$fatal(1,"directacceptedwriteburstnotfullystored");
   end
   checks=checks+1;aborts=aborts+1;
  end
  // Read-data abort at every one of32accepted responsebeats. A full tile
  // is never exposed from a canceled transaction; accepted BL8alwaysdrains.
  for(k=1;k<=32;k=k+1)begin: read_abort_all
   integer old_beats,old_reads;old_beats=pin_read_beats;old_reads=completed_reads;
   @(negedge clk);read_valid=1;read_generation=2000+k;read_bank=2;read_plane=2;read_index=1349;
   do @(posedge clk);while(!read_ready);
   @(negedge clk);read_valid=0;
   while(pin_read_beats-old_beats<k)@(negedge clk);
   abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(read_rsp_valid||write_done_valid)$fatal(1,"directreadabortsuccessleak");@(negedge clk);end
   if(!tile_aborted||completed_reads-old_reads!=(k+7)/8)$fatal(1,"directreadabortdraincount");
   checks=checks+1;aborts=aborts+1;
  end
  $display("CU71_DIRECT_ABORT_ALL_PASS write_positions=32 read_positions=32");
  prior_refreshes=model.refreshes;repeat(1600)@(negedge clk);if(model.refreshes<=prior_refreshes)$fatal(1,"refresh idle not exercised");
  if(model.mem[CANONICAL0_BASE-1]!==16'hcafe||model.mem[24'(CANONICAL0_BASE+CANONICAL0_WORDS)]!==16'hbabe)$fatal(1,"guard corrupted");
  if(completed_reads!=32'(model.reads)||completed_writes*8!=32'(model.writes))$fatal(1,"completedcommandcounts");
  if(cache_hits==0||cache_misses==0||model.acts==0||model.pres==0||model.refreshes<4)$fatal(1,"command/cache coverage");
  if(observed_LCD!=dut.bridge.group_lcd_accepted||observed_BG!=dut.bridge.group_bg_accepted)$fatal(1,"quota chargednonphysical/localoperation");
  $display("CU71_GROUPED_ACCOUNTING_PASS LCD=%0d BG=%0d uncharged=%0d idle=%0d LCD_idle=%0d BG_idle=%0d LCD_expiry=%0d BG_expiry=%0d max_LCD_wait=%0d max_BG_wait=%0d",observed_LCD,observed_BG,dut.bridge.group_uncharged,dut.bridge.group_reserved_idle,dut.bridge.group_lcd_reserved_idle,dut.bridge.group_bg_reserved_idle,dut.bridge.group_lcd_expiry,dut.bridge.group_bg_expiry,lcd_max_wait,dut.bridge.group_bg_max_wait);
  $display("CU71_DIRECT_MEMORY_PASS seed=%0d checks=%0d tiles=%0d aux=%0d aborts=%0d cycles=%0d writes=%0d reads=%0d ACT=%0d PRE=%0d REF=%0d cache_hits=%0d cache_misses=%0d max_aux_wait=%0d",seed,checks,tiles,aux_ops,aborts,cycles,model.writes,model.reads,model.acts,model.pres,model.refreshes,cache_hits,cache_misses,max_aux_wait);
  $finish;
 end
 initial begin #100000000;$fatal(1,"memory test watchdog");end
endmodule
