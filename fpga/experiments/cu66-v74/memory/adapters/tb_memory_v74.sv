`timescale 1ns/1ps
module tb_memory_v74 #(parameter real TAC_NS=2.0,FLIGHT_NS=4.0);
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
 integer lcd_bursts=0,lcd_words=0,lcd_rejects=0,max_lcd_service=0,max_lcd_streak=0;
 integer lcd_streak_probe=0,scalar_grants=0,lcd_line_min=1000000,lcd_line_max=0;
 integer lcd_bubble=0,lcd_adversarial=0,grace_blocks=0,silent_wait=0;
 always @(posedge clk)begin
  if(rst)lcd_streak_probe=0;
  else begin
   if(dut.bridge.lcd_grace&&!lcd_req_valid&&dut.bridge.state==0&&(dut.bridge.p0_valid||dut.bridge.p1_valid))begin
    if(dut.bridge.p0_ready||dut.bridge.p1_ready)$fatal(1,"LCD grace failed to hold scalar grant");
    grace_blocks=grace_blocks+1;
   end
   if(dut.bridge.p0_valid&&dut.bridge.p0_ready || dut.bridge.p1_valid&&dut.bridge.p1_ready)begin
    scalar_grants=scalar_grants+1;lcd_streak_probe=0;
   end else if(lcd_req_valid&&lcd_req_ready)begin
    if(dut.bridge.p0_valid||dut.bridge.p1_valid)begin
     lcd_streak_probe=lcd_streak_probe+1;
     if(lcd_streak_probe>4)$fatal(1,"LCD exceeded four-grant bound with scalar waiting");
     if(lcd_streak_probe>max_lcd_streak)max_lcd_streak=lcd_streak_probe;
    end else lcd_streak_probe=0;
   end
  end
 end
 task automatic lcd_burst(input logic[23:0]address,input bit expect_bad,input integer stall);
  integer started,word_no;logic[15:0]saved;
  begin
   @(negedge clk);lcd_req_valid=1;lcd_req_addr=address;
   do @(posedge clk);while(!lcd_req_ready);
   started=cycles;
   @(negedge clk);lcd_req_valid=0;
   for(word_no=0;word_no<8;word_no=word_no+1)begin
    while(!lcd_rsp_valid)@(negedge clk);
    if(!lcd_busy)$fatal(1,"LCD response without busy");
    saved=lcd_rsp_data;
    if(lcd_rsp_error!==expect_bad||lcd_rsp_last!==(word_no==7))$fatal(1,"LCD framing/error mismatch");
    if(!expect_bad&&saved!==model.mem[address+24'(word_no)])$fatal(1,"LCD data address %h word %0d got %h",address,word_no,saved);
    if(expect_bad&&saved!==0)$fatal(1,"LCD rejected data was nonzero");
    repeat(stall>0?stall+((word_no==0||word_no==3||word_no==7)?17:0):0)begin
     @(negedge clk);
     if(!lcd_rsp_valid||lcd_rsp_data!==saved||lcd_rsp_error!==expect_bad||lcd_rsp_last!==(word_no==7))$fatal(1,"LCD held response changed");
    end
    lcd_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;
    lcd_words=lcd_words+1;checks=checks+1;
   end
   if(cycles-started>max_lcd_service)max_lcd_service=cycles-started;
   lcd_bursts=lcd_bursts+1;if(expect_bad)lcd_rejects=lcd_rejects+1;
  end
 endtask

 cu74_memory_system #(.POWERUP_CYCLES(20)) dut(.*);
 cu72_sdram_model #(.T_AC_NS(TAC_NS),.CLOCK_FLIGHT_NS(FLIGHT_NS)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 `include "cu70_memory_map.svh"
 integer observed_writes=0;
 always @(negedge clk)begin
  if(rst)observed_writes=0;
  else if(model.writes!=observed_writes)begin
   if(model.writes!=observed_writes+1||model.mem[model.last_write_address]!==model.last_write_data)$fatal(1,"model write event framing");
   observed_writes=model.writes;
  end
 end
 integer checks=0,tiles=0,aux_ops=0,aborts=0,cycles=0;
 integer seed=7001,seed_input,max_aux_wait=0;
 logic[511:0]pattern;
 logic[15:0]got;
 integer b,p,t,j,k,idx,base,address0,prior_writes,prior_refreshes;
 always @(posedge clk)cycles=cycles+1;
 function automatic logic[511:0]make_pattern(input integer salt);
  for(integer i=0;i<64;i=i+1)make_pattern[8*i+:8]=8'((salt*37+i*19)^(i/8));
 endfunction
 task automatic aux(input bit writing,input logic[23:0]address,input logic[15:0]data,input bit expect_bad,output logic[15:0]result);
  logic[15:0]saved;integer wait_count;
  begin
   @(negedge clk);aux_req_burst=0;aux_req_burst_data=0;aux_req_byte_enable=0;aux_req_valid=1;aux_req_write=writing;aux_req_addr=address;aux_req_data=data;
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;wait_count=0;
   while(!aux_rsp_valid)begin @(negedge clk);wait_count=wait_count+1;if(wait_count>2000)$fatal(1,"aux watchdog address%h",address);end
   if(wait_count>max_aux_wait)max_aux_wait=wait_count;
   if(aux_rsp_error!==expect_bad)$fatal(1,"aux error address%h got%b expected%b",address,aux_rsp_error,expect_bad);
   saved=aux_rsp_data;
   if(!writing&&!expect_bad&&aux_rsp_burst_data[address[2:0]*16+:16]!==saved)$fatal(1,"scalar/full P1 snapshot mismatch");
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
   if(model.writes-before_count>8)$fatal(1,"abort started additional tile blocks");
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

 integer burst_checks=0,burst_aborts=0;
 task automatic wide(input bit writing,input logic[23:0]address,input logic[127:0]data,input logic[15:0]mask,input bit expect_bad);
  integer initial_commands;logic[15:0]saved;
  begin
   initial_commands=model.write_commands;
   @(negedge clk);aux_req_burst=1;aux_req_valid=1;aux_req_write=writing;aux_req_addr=address;aux_req_burst_data=data;aux_req_byte_enable=mask;
   do @(posedge clk);while(!aux_req_ready);
   // Change all producer payload after acceptance; the wrapper owns a snapshot.
   @(negedge clk);aux_req_valid=0;aux_req_burst=0;aux_req_burst_data=~data;aux_req_byte_enable=~mask;aux_req_addr=0;
   while(!aux_rsp_valid)@(negedge clk);
   if(aux_rsp_error!==expect_bad)$fatal(1,"wide error addr%h expected%b",address,expect_bad);
   if(!expect_bad&&writing&&model.write_commands!=initial_commands+1)$fatal(1,"wide command count");
   if(expect_bad&&model.write_commands!=initial_commands)$fatal(1,"rejected wide reached controller");
   if(!expect_bad&&writing&&(model.write_left!=0||model.cycle-model.lastwrite[address[23:22]]<2))$fatal(1,"write acknowledged before recovery");
   saved=aux_rsp_data;
   repeat(5)begin @(negedge clk);if(!aux_rsp_valid||aux_rsp_error!==expect_bad||aux_rsp_data!==saved)$fatal(1,"wide held response changed");end
   aux_rsp_ready=1;@(posedge clk);@(negedge clk);aux_rsp_ready=0;aux_req_burst=0;burst_checks=burst_checks+1;checks=checks+1;
  end
 endtask
 task automatic burst_campaign;
  logic[127:0]payload;logic[15:0]value,want;logic[511:0]tile_payload;integer n,mask_case,first_commands,base_words,offset,plane_no,word_no,row_address;
  begin
   for(n=0;n<8;n=n+1)aux(1,DIAGNOSTIC_BASE+24'd4096+24'(n),16'hcafe,0,value);
   // Prime p1 cache, then exercise complete and partial byte masks. Immutable
   // snapshots and actual scalar reads ensure inactive neighbors survive.
   for(mask_case=0;mask_case<5;mask_case=mask_case+1)begin
    for(n=0;n<8;n=n+1)payload[n*16+:16]=16'(32'h1230+mask_case*257+n);
    wide(1,DIAGNOSTIC_BASE+24'd4096,payload,mask_case==0?16'hffff:mask_case==1?16'h00ff:mask_case==2?16'hff00:mask_case==3?16'h5555:16'haaaa,0);
    for(n=0;n<8;n=n+1)begin
     aux(0,DIAGNOSTIC_BASE+24'd4096+24'(n),0,0,value);
     if(mask_case==0)want=16'(32'h1230+n);
     else if(mask_case==1)want=n<4?16'(32'h1331+n):16'(32'h1230+n);
     else if(mask_case==2)want=n<4?16'(32'h1331+n):16'(32'h1432+n);
     else if(mask_case==3)want={8'(n<4?19:20),8'(32'h1533+n)};
     else want={8'(22),8'(32'h1533+n)};
     if(value!==want)$fatal(1,"wide mask neighbor mismatch case%0d n%0d got%h want%h",mask_case,n,value,want);
     checks=checks+1;
    end
   end
   first_commands=model.write_commands;
   wide(1,DIAGNOSTIC_BASE+24'd4097,payload,16'hffff,1);
   wide(1,DIAGNOSTIC_BASE+24'd4096,payload,0,1);
   wide(0,DIAGNOSTIC_BASE+24'd4096,payload,16'hffff,1);
   wide(1,CANONICAL0_BASE-24'd8,payload,16'hffff,1);
   if(model.write_commands!=first_commands)$fatal(1,"invalid burst changed memory");
   // Every accepted physical BL8 beat boundary is canceled at the wrapper.
   // Once issued, all eight writes must finish and only then signal aborted.
   for(offset=0;offset<8;offset=offset+1)begin
    base_words=model.write_bus_beats;
    @(negedge clk);aux_req_burst=1;aux_req_valid=1;aux_req_write=1;aux_req_addr=DIAGNOSTIC_BASE+24'd8192+24'(offset*8);aux_req_burst_data={8{16'(32'hb100+offset)}};aux_req_byte_enable=16'hffff;
    do @(posedge clk);while(!aux_req_ready);
    @(negedge clk);aux_req_valid=0;aux_req_burst=0;
    while(model.write_bus_beats<base_words+offset+1)@(negedge clk);
    aux_abort_i=1;@(posedge clk);@(negedge clk);aux_abort_i=0;
    while(aux_busy)begin if(aux_rsp_valid)$fatal(1,"aborted wide exposed response");@(negedge clk);end
    if(!aux_aborted||model.write_bus_beats!=base_words+8||model.write_left!=0)$fatal(1,"wide abort failed visible drain");
    for(n=0;n<8;n=n+1)begin
     aux(0,DIAGNOSTIC_BASE+24'd8192+24'(offset*8+n),0,0,value);
     if(value!==16'(32'hb100+offset))$fatal(1,"wide abort lost accepted beat");
    end
    burst_aborts=burst_aborts+1;burst_checks=burst_checks+1;
   end
   // Full aligned tile blocks retain independent sentinels on each side.
   for(plane_no=0;plane_no<3;plane_no=plane_no+1)begin
    for(offset=0;offset<2;offset=offset+1)begin
     tile_payload=make_pattern(7230+plane_no*10+offset);
     row_address=524288+(plane_no==0?0:plane_no==1?172800:216000)+(12+offset*3)*32;
     for(word_no=-1;word_no<=32;word_no=word_no+1)aux(1,24'(row_address+word_no),16'h5a5a,0,value);
     first_commands=model.write_commands;
     write_tile(0,plane_no,12+offset*3,tile_payload,0);
     if(model.write_commands-first_commands!=4)$fatal(1,"canonical tile writer did not use four bursts");
     for(word_no=-1;word_no<=32;word_no=word_no+1)begin
      aux(0,24'(row_address+word_no),0,0,value);
      want=(word_no>=0&&word_no<32)?tile_payload[word_no*16+:16]:16'h5a5a;
      if(value!==want)$fatal(1,"tile-major sentinel/layout plane%0d word%0d",plane_no,word_no);
     end
     burst_checks=burst_checks+1;
    end
   end
  end
 endtask

 integer wide_read_checks=0,wide_read_aborts=0,read_bus_beats=0;
 always @(posedge clk)begin
  if(rst)read_bus_beats=0;else if(dut.mem_rsp_valid)read_bus_beats=read_bus_beats+1;
 end
 task automatic wide_read(input logic[23:0]address,input logic[127:0]expected,input bit wr,bflags,bad);
  logic[127:0]saved;integer reads0,writes0;
  begin
   reads0=model.reads;writes0=model.write_commands;
   @(negedge clk);aux_req_read_burst=1;aux_req_burst=bflags;aux_req_write=wr;aux_req_valid=1;aux_req_addr=address;aux_req_byte_enable=16'hffff;
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;aux_req_read_burst=0;aux_req_burst=0;aux_req_write=0;aux_req_addr=0;aux_req_byte_enable=0;aux_req_data=16'hdeaf;aux_req_burst_data=~expected;
   while(!aux_rsp_valid)@(negedge clk);
   saved=aux_rsp_burst_data;
   if(aux_rsp_error!==bad)$fatal(1,"P1 wide error mismatch addr%h",address);
   if(!bad&&(saved!==expected||aux_rsp_data!==expected[15:0]))$fatal(1,"P1 wide payload mismatch addr%h got%h expected%h",address,saved,expected);
   if(bad&&(saved!==0||model.reads!=reads0||model.write_commands!=writes0))$fatal(1,"P1 rejected request issued command or exposed data");
   repeat(32)begin @(negedge clk);if(!aux_busy||!aux_rsp_valid||aux_rsp_burst_data!==saved||aux_rsp_error!==bad)$fatal(1,"P1 held full response changed");end
   aux_rsp_ready=1;@(posedge clk);@(negedge clk);aux_rsp_ready=0;wide_read_checks=wide_read_checks+1;
  end
 endtask
 task automatic wide_read_campaign;
  logic[127:0]expected;logic[15:0]unused_value;integer n,offset,before_beats,rows0,reads0;
  begin
   rows0=int'(p0_row_reads);
   for(n=0;n<8;n=n+1)begin
    expected[n*16+:16]=16'(32'he100+n*73);
    aux(1,DIAGNOSTIC_BASE+24'd16384+24'(n),expected[n*16+:16],0,unused_value);
   end
   reads0=model.reads;
   wide_read(DIAGNOSTIC_BASE+24'd16384,expected,0,0,0);
   if(model.reads!=reads0+1)$fatal(1,"wrapper wide miss command count");
   reads0=model.reads;
   wide_read(DIAGNOSTIC_BASE+24'd16384,expected,0,0,0);
   if(model.reads!=reads0)$fatal(1,"wrapper wide cache hit issued command");
   wide_read(DIAGNOSTIC_BASE+24'd16388,0,0,0,1);
   wide_read(DIAGNOSTIC_BASE+24'd16385,0,0,0,1);
   wide_read(0,0,0,0,1);
   wide_read(CANONICAL2_BASE+24'(CANONICAL2_WORDS),0,0,0,1);
   wide_read(DIAGNOSTIC_BASE+24'd16384,0,1,0,1);
   wide_read(DIAGNOSTIC_BASE+24'd16384,0,0,1,1);
   wide_read(DIAGNOSTIC_BASE+24'd16384,0,1,1,1);
   // Abort on each accepted physical read beat; the wrapper drains all eight
   // beats and suppresses a response. Use fresh physical lines to force misses.
   for(offset=0;offset<8;offset=offset+1)begin
    for(n=0;n<8;n=n+1)begin
     expected[n*16+:16]=16'(32'hc500+offset*91+n);
     aux(1,DIAGNOSTIC_BASE+24'd17408+24'(offset*8+n),expected[n*16+:16],0,unused_value);
    end
    before_beats=read_bus_beats;
    @(negedge clk);aux_req_read_burst=1;aux_req_write=0;aux_req_burst=0;aux_req_valid=1;aux_req_addr=DIAGNOSTIC_BASE+24'd17408+24'(offset*8);
    do @(posedge clk);while(!aux_req_ready);
    @(negedge clk);aux_req_valid=0;aux_req_read_burst=0;aux_req_addr=0;
    while(read_bus_beats<before_beats+offset+1)@(negedge clk);
    aux_abort_i=1;@(posedge clk);@(negedge clk);aux_abort_i=0;
    while(aux_busy)begin if(aux_rsp_valid)$fatal(1,"P1 aborted read exposed response");@(negedge clk);end
    if(!aux_aborted||read_bus_beats!=before_beats+8)$fatal(1,"P1 wide abort failed full read drain");
    wide_read_aborts=wide_read_aborts+1;
    wide_read(DIAGNOSTIC_BASE+24'd17408+24'(offset*8),expected,0,0,0);
   end
   // Abort while admitted by the wrapper but before bridge acceptance.
   reads0=model.reads;
   @(negedge clk);aux_req_valid=1;aux_req_read_burst=1;aux_req_write=0;aux_req_burst=0;aux_req_addr=DIAGNOSTIC_BASE+24'd18000;
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;aux_req_read_burst=0;aux_abort_i=1;
   @(posedge clk);@(negedge clk);aux_abort_i=0;
   if(aux_busy||!aux_aborted||aux_rsp_valid||model.reads!=reads0)$fatal(1,"P1 preissue abort failed");
   wide_read_aborts=wide_read_aborts+1;
   if(p0_row_reads!=32'(rows0))$fatal(1,"P1 wide operation charged P0 row counter");
  end
 endtask

 initial begin
  if(!$test$plusargs("RESET_ONLY"))begin
  if($value$plusargs("SEED=%d",seed_input))seed=seed_input;
  if($value$plusargs("LCD_BUBBLE=%d",lcd_bubble))begin end
  if($value$plusargs("LCD_ADVERSARIAL=%d",lcd_adversarial))begin end
  // Guard sentinels live outside the public allocation ranges.
  for(b=0;b<3;b=b+1)begin
   model.mem[(b==0?524288:b==1?4718592:8912896)-1]=16'hcafe;model.mem[(b==0?524288:b==1?4718592:8912896)+259200]=16'hbabe;
  end
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
   base=(b==0?524288:b==1?4718592:8912896)+(p==0?0:p==1?172800:216000)+idx*32;
   for(j=0;j<32;j=j+1)begin
    address0=base+j;if(address0<0||address0>=16777216)$fatal(1,"scalaroracleaddress");aux(0,24'(address0),0,0,got);
    if(got!==pattern[16*j+:16])$fatal(1,"scalar layout mismatch");
   end
  end
  pattern=make_pattern(555);write_tile(0,0,0,pattern,0);aux(0,CANONICAL0_BASE,0,0,got);
  pattern[15:0]=16'h4321;write_tile(0,0,0,pattern,0);aux(0,CANONICAL0_BASE,0,0,got);if(got!==16'h4321)$fatal(1,"cross-client cache stale");read_tile(0,0,0,pattern,0);
  prior_writes=model.writes;
  write_tile(3,0,0,0,1);write_tile(0,3,0,0,1);write_tile(0,0,5400,0,1);read_tile(0,1,1350,0,1);
  if(model.writes!=prior_writes)$fatal(1,"invalid tile reachedSDRAM");
  burst_campaign();
  wide_read_campaign();
  for(k=0;k<=32;k=k+1)abort_write(k);
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
  // Independent LCD port: full aligned bursts at every internal bank and the
  // very last physical BL8; model.mem is a read-only assertion oracle here.
  for(b=0;b<4;b=b+1)begin
   address0=b==0?int'(CANONICAL0_BASE):b==1?int'(CANONICAL1_BASE):b==2?int'(CANONICAL2_BASE):int'(DIAGNOSTIC_BASE);
   for(j=0;j<8;j=j+1)aux(1,24'(address0+j),16'(32'h7100+b*13+j),0,got);
   lcd_burst(24'(address0),0,3);
  end
  for(j=0;j<8;j=j+1)aux(1,24'hfffff8+24'(j),16'(32'hff00+j),0,got);
  lcd_burst(24'hfffff8,0,1);
  prior_writes=model.reads;
  lcd_burst(RGB0_BASE+1,1,2);lcd_burst(0,1,0);
  lcd_burst(CANONICAL0_BASE+24'(CANONICAL0_WORDS),1,1);
  if(model.reads!=prior_writes)$fatal(1,"rejected LCD burst reached SDRAM");
  // Initialize RGB words through the checked scalar interface, never by a
  // memory-model backdoor, before continuous LCD data checks.
  for(j=0;j<1920;j=j+1)aux(1,RGB0_BASE+24'(j),16'(j*193+7101),0,got);
  // Four interleaved scalar working sets must coexist in the p1 cache.
  for(j=0;j<4;j=j+1)aux(0,DIAGNOSTIC_BASE+24'(j*512),0,0,got);
  prior_writes=model.reads;
  for(k=0;k<4;k=k+1)for(j=0;j<4;j=j+1)aux(0,DIAGNOSTIC_BASE+24'(j*512+1),0,0,got);
  if(model.reads!=prior_writes)$fatal(1,"four-way scalar working set thrashed");
  // Accepted scalar alias writes invalidate all matching cache entries.
  aux(1,DIAGNOSTIC_BASE+24'd513,16'hbeef,0,got);
  aux(0,DIAGNOSTIC_BASE+24'd513,0,0,got);if(got!==16'hbeef)$fatal(1,"p1 alias invalidation");
  lcd_burst(DIAGNOSTIC_BASE+24'd512,0,0);
  // Continuous LCD work plus actual tile writes and scalar aux traffic.
  // Grant-bound counters are checked independently of per-client data checks.
  fork
   begin : continuous_lcd
    integer line_no,burst_no,line_start,line_elapsed,word_no,started;
    @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE;lcd_rsp_ready=1;
    for(line_no=0;line_no<4;line_no=line_no+1)begin
     line_start=cycles;
     for(burst_no=0;burst_no<60;burst_no=burst_no+1)begin
      do @(posedge clk);while(!lcd_req_ready);
      started=cycles;
      @(negedge clk);
      for(word_no=0;word_no<8;word_no=word_no+1)begin
       do @(posedge clk);while(!lcd_rsp_valid);
       if(lcd_rsp_error||lcd_rsp_last!==(word_no==7)||lcd_rsp_data!==model.mem[lcd_req_addr+24'(word_no)])$fatal(1,"continuous LCD data/framing");
       lcd_words=lcd_words+1;checks=checks+1;
       @(negedge clk);
      end
      if(cycles-started>max_lcd_service)max_lcd_service=cycles-started;
      lcd_bursts=lcd_bursts+1;
      lcd_req_addr=lcd_req_addr+8;
      // Extra idle request clocks conservatively model a non-continuous
      // adapter; the scalar client can take the bus in the gap.
      if(lcd_bubble>0)begin
       lcd_req_valid=0;repeat(lcd_bubble)@(negedge clk);lcd_req_valid=1;
      end
     end
     line_elapsed=cycles-line_start;
     if(line_elapsed<lcd_line_min)lcd_line_min=line_elapsed;
     if(line_elapsed>lcd_line_max)lcd_line_max=line_elapsed;
    end
    lcd_req_valid=0;lcd_rsp_ready=0;
   end
   begin
    integer tile_no;
    for(tile_no=0;tile_no<4;tile_no=tile_no+1)write_tile(2,0,300+tile_no,make_pattern(7171+tile_no),0);
   end
   begin
    integer n;logic[15:0]value;
    for(n=0;n<96;n=n+1)begin
     aux(1,lcd_adversarial!=0?RGB1_BASE+24'((n%2)*512+n/2):HUD0_BASE+24'(n),16'(n+71),0,value);
     aux(0,lcd_adversarial!=0?RGB1_BASE+24'((n%2)*512+n/2):HUD0_BASE+24'(n),0,0,value);
     if(value!==16'(n+71))$fatal(1,"LCD concurrency corrupted aux");
    end
   end
  join
  if(lcd_bubble==0&&max_lcd_streak!=4)$fatal(1,"LCD fairness saturation not covered");
  if(lcd_line_max>1842)$fatal(1,"normal LCD line exceeded native 1842.54-clock period: %0d",lcd_line_max);
  // A producer that stops after one LCD burst cannot reserve the arbiter
  // indefinitely. Admit scalar aux concurrently with the last LCD beat so its
  // bridge request actually encounters grace, then require finite completion.
  aux(0,RGB0_BASE,0,0,got); // known cached read, independent of SDRAM row phase
  fork
   begin lcd_burst(RGB0_BASE,0,0);end
   begin : silent_producer_scalar
    while(!(lcd_rsp_valid&&lcd_rsp_last))@(negedge clk);
    aux_req_valid=1;aux_req_write=0;aux_req_addr=RGB0_BASE;aux_req_data=0;
    do @(posedge clk);while(!aux_req_ready);
    @(negedge clk);aux_req_valid=0;silent_wait=0;
    while(!aux_rsp_valid)begin
     @(negedge clk);silent_wait=silent_wait+1;
     if(silent_wait>80)$fatal(1,"silent LCD producer starved scalar service");
    end
    if(aux_rsp_error||aux_rsp_data!==16'd7101)$fatal(1,"silent producer scalar data");
    aux_rsp_ready=1;@(posedge clk);@(negedge clk);aux_rsp_ready=0;aux_ops=aux_ops+1;checks=checks+1;
   end
  join
  if(grace_blocks==0)$fatal(1,"LCD grace collision not exercised");
  prior_refreshes=model.refreshes;repeat(1600)@(negedge clk);if(model.refreshes<=prior_refreshes)$fatal(1,"refresh idle not exercised");
  for(b=0;b<3;b=b+1)if(model.mem[(b==0?524288:b==1?4718592:8912896)-1]!==16'hcafe||model.mem[(b==0?524288:b==1?4718592:8912896)+259200]!==16'hbabe)$fatal(1,"bank guard corrupted");
  if(completed_reads!=32'(model.reads)||completed_writes!=32'(model.write_commands))$fatal(1,"completedcommandcounts");
  if(cache_hits==0||cache_misses==0||model.acts==0||model.pres==0||model.refreshes<4)$fatal(1,"command/cache coverage");
  if(p0_cache_hits+p1_cache_hits!=cache_hits||p0_cache_misses+p1_cache_misses!=cache_misses||p0_row_reads==0||p0_read_wait_cycles>p0_wait_cycles||p0_read_service_cycles>p0_service_cycles)$fatal(1,"profile accounting");
  $display("MEMORY_V74_PROFILE p0_hits=%0d p0_misses=%0d row_reads=%0d p0_wait=%0d p0_service=%0d p1_hits=%0d p1_misses=%0d read_wait=%0d read_service=%0d",p0_cache_hits,p0_cache_misses,p0_row_reads,p0_wait_cycles,p0_service_cycles,p1_cache_hits,p1_cache_misses,p0_read_wait_cycles,p0_read_service_cycles);
  $display("MEMORY_V74_PASS seed=%0d checks=%0d tiles=%0d aux=%0d aborts=%0d wide_read_checks=%0d wide_read_aborts=%0d cycles=%0d writes=%0d write_commands=%0d write_bus_beats=%0d burst_checks=%0d burst_aborts=%0d reads=%0d ACT=%0d PRE=%0d REF=%0d cache_hits=%0d cache_misses=%0d max_aux_wait=%0d lcd_bursts=%0d lcd_words=%0d lcd_rejects=%0d max_lcd_service=%0d max_lcd_streak=%0d scalar_grants=%0d lcd_line_min=%0d lcd_line_max=%0d lcd_bubble=%0d lcd_adversarial=%0d grace_blocks=%0d silent_wait=%0d",seed,checks,tiles,aux_ops,aborts,wide_read_checks,wide_read_aborts,cycles,model.writes,model.write_commands,model.write_bus_beats,burst_checks,burst_aborts,model.reads,model.acts,model.pres,model.refreshes,cache_hits,cache_misses,max_aux_wait,lcd_bursts,lcd_words,lcd_rejects,max_lcd_service,max_lcd_streak,scalar_grants,lcd_line_min,lcd_line_max,lcd_bubble,lcd_adversarial,grace_blocks,silent_wait);
  $finish;
  end
 end
 initial begin : reset_campaign
  integer probe,held_word,delivered;
  logic[15:0]saved,value;
  if($test$plusargs("RESET_ONLY"))begin
   repeat(5)@(negedge clk);rst=0;while(!idle)@(negedge clk);
   for(integer n=0;n<8;n=n+1)begin
    aux(1,RGB0_BASE+24'(n),16'(32'h7100+n),0,value);
    aux(0,RGB0_BASE+24'(n),0,0,value);
    if(value!==16'(32'h7100+n))$fatal(1,"reset campaign initialization");
   end
   for(probe=0;probe<4;probe=probe+1)begin
    held_word=probe==0?0:probe==1?3:probe==2?7:0;
    @(negedge clk);lcd_req_valid=1;lcd_req_addr=probe==3?24'd0:RGB0_BASE;lcd_rsp_ready=0;
    do @(posedge clk);while(!lcd_req_ready);
    @(negedge clk);lcd_req_valid=0;
    for(delivered=0;delivered<held_word;delivered=delivered+1)begin
     lcd_rsp_ready=1;do @(posedge clk);while(!lcd_rsp_valid);
     @(negedge clk);lcd_rsp_ready=0;
    end
    while(!lcd_rsp_valid)@(negedge clk);
    saved=lcd_rsp_data;
    repeat(32)begin
     @(negedge clk);
     if(!lcd_rsp_valid||!lcd_busy||idle||lcd_rsp_data!==saved||lcd_rsp_last!==(held_word==7)||lcd_rsp_error!==(probe==3))$fatal(1,"long LCD stall/idle contract");
    end
    rst=1;repeat(5)begin
     @(negedge clk);if(lcd_rsp_valid||lcd_req_ready||lcd_busy)$fatal(1,"reset retained LCD lease");
    end
    rst=0;while(!idle)@(negedge clk);
    repeat(10)begin @(negedge clk);if(lcd_rsp_valid||lcd_busy)$fatal(1,"stale LCD response after reset");end
    lcd_burst(RGB0_BASE,0,0);
   end
   $display("MEMORY_V74_RESET_PASS probes=4 hold_clocks=32 held_positions=0_3_7_invalid fresh_bursts=%0d fresh_words=%0d",lcd_bursts,lcd_words);
   $finish;
  end
 end
 initial begin #100000000;$fatal(1,"memory test watchdog");end
endmodule
