`timescale 1ns/1ps
module tb_memory_v81 #(parameter real TAC_NS=2.0);
 logic  clk=0;
 logic  read_clk=0;
 logic  rst=0;
 logic  abort_i=0;
 logic  unused_aux_abort_i=0;
 logic  unused_read_valid=0;
 logic  unused_read_ready;
 logic [63:0] unused_read_generation=0;
 logic [1:0] unused_read_bank=0;
 logic [1:0] unused_read_plane=0;
 logic [16:0] unused_read_index=0;
 logic  unused_read_rsp_valid;
 logic  unused_read_rsp_ready=0;
 logic [63:0] unused_read_rsp_generation;
 logic [1:0] unused_read_rsp_bank;
 logic [1:0] unused_read_rsp_plane;
 logic [16:0] unused_read_rsp_index;
 logic [511:0] unused_read_rsp_pixels;
 logic  unused_read_rsp_error;
 logic  write_valid=0;
 logic  write_ready;
 logic [63:0] write_generation=0;
 logic [1:0] write_bank=0;
 logic [1:0] write_plane=0;
 logic [16:0] write_index=0;
 logic [511:0] write_pixels=0;
 logic  write_done_valid;
 logic  write_done_ready=0;
 logic [63:0] unused_write_done_generation;
 logic [1:0] unused_write_done_bank;
 logic [1:0] unused_write_done_plane;
 logic [16:0] unused_write_done_index;
 logic  write_done_error;
 logic  tile_busy;
 logic  tile_aborted;
 logic  aux_req_valid=0;
 logic  aux_req_ready;
 logic  unused_aux_req_write=0;
 logic [23:0] aux_req_addr=0;
 logic [15:0] unused_aux_req_data=0;
 logic  unused_aux_req_read_burst=0;
 logic [127:0] unused_aux_rsp_burst_data;
 logic  unused_aux_req_burst=0;
 logic [127:0] unused_aux_req_burst_data=0;
 logic [15:0] unused_aux_req_byte_enable=0;
 logic  aux_rsp_valid;
 logic  aux_rsp_ready=0;
 logic [15:0] aux_rsp_data;
 logic  aux_rsp_error;
 logic  unused_aux_busy;
 logic  unused_aux_aborted;
 logic  lcd_req_valid=0;
 logic  lcd_req_ready;
 logic [23:0] lcd_req_addr=0;
 logic  lcd_rsp_valid;
 logic  lcd_rsp_ready=0;
 logic [15:0] lcd_rsp_data;
 logic  lcd_rsp_last;
 logic  lcd_rsp_error;
 logic  unused_lcd_busy;
 logic [31:0] unused_cache_hits;
 logic [31:0] unused_cache_misses;
 logic [31:0] unused_completed_reads;
 logic [31:0] unused_completed_writes;
 logic [31:0] unused_p0_cache_hits;
 logic [31:0] unused_p0_cache_misses;
 logic [31:0] unused_p0_row_reads;
 logic [31:0] unused_p0_wait_cycles;
 logic [31:0] unused_p0_service_cycles;
 logic [31:0] unused_p1_cache_hits;
 logic [31:0] unused_p1_cache_misses;
 logic [31:0] unused_p0_read_wait_cycles;
 logic [31:0] unused_p0_read_service_cycles;
 wire [12:0] sdram_a;
 wire [1:0] sdram_bs;
 wire [1:0] sdram_cke;
 wire [1:0] sdram_cs_n;
 wire [15:0] sdram_dq;
 wire  sdram_clk;
 wire  sdram_ras_n;
 wire  sdram_cas_n;
 wire  sdram_we_n;
 wire  sdram_ldqm;
 wire  sdram_udqm;
 logic  prefetch_req_valid=0;
 logic  prefetch_req_ready;
 logic [23:0] prefetch_req_address=0;
 logic  prefetch_rsp_valid;
 logic  prefetch_rsp_ready=0;
 logic [127:0] prefetch_rsp_data;
 logic [63:0] prefetch_req_generation=0,prefetch_rsp_generation,expected_generation=0;
 logic [1:0] prefetch_req_bank=0,prefetch_req_plane=0,prefetch_req_block=0,prefetch_rsp_bank,prefetch_rsp_plane,prefetch_rsp_block,expected_bank=0,expected_plane=0,expected_block=0;
 logic [16:0] prefetch_req_index=0,prefetch_rsp_index,expected_index=0;
 logic  prefetch_rsp_error;
 logic  prefetch_busy;
 logic  command_valid;
 logic  command_write;
 logic [23:0] command_address;
 logic [1:0] command_client;
 logic  idle;
 always #5 clk=~clk;
 always @(clk)read_clk<=#2.75 ~clk;
 cu81_memory_system #(.POWERUP_CYCLES(20)) dut(
 .clk(clk),
 .read_clk(read_clk),
 .rst(rst),
 .abort_i(abort_i),
 .aux_abort_i(unused_aux_abort_i),
 .read_valid(unused_read_valid),
 .read_ready(unused_read_ready),
 .read_generation(unused_read_generation),
 .read_bank(unused_read_bank),
 .read_plane(unused_read_plane),
 .read_index(unused_read_index),
 .read_rsp_valid(unused_read_rsp_valid),
 .read_rsp_ready(unused_read_rsp_ready),
 .read_rsp_generation(unused_read_rsp_generation),
 .read_rsp_bank(unused_read_rsp_bank),
 .read_rsp_plane(unused_read_rsp_plane),
 .read_rsp_index(unused_read_rsp_index),
 .read_rsp_pixels(unused_read_rsp_pixels),
 .read_rsp_error(unused_read_rsp_error),
 .write_valid(write_valid),
 .write_ready(write_ready),
 .write_generation(write_generation),
 .write_bank(write_bank),
 .write_plane(write_plane),
 .write_index(write_index),
 .write_pixels(write_pixels),
 .write_done_valid(write_done_valid),
 .write_done_ready(write_done_ready),
 .write_done_generation(unused_write_done_generation),
 .write_done_bank(unused_write_done_bank),
 .write_done_plane(unused_write_done_plane),
 .write_done_index(unused_write_done_index),
 .write_done_error(write_done_error),
 .tile_busy(tile_busy),
 .tile_aborted(tile_aborted),
 .aux_req_valid(aux_req_valid),
 .aux_req_ready(aux_req_ready),
 .aux_req_write(unused_aux_req_write),
 .aux_req_addr(aux_req_addr),
 .aux_req_data(unused_aux_req_data),
 .aux_req_read_burst(unused_aux_req_read_burst),
 .aux_rsp_burst_data(unused_aux_rsp_burst_data),
 .aux_req_burst(unused_aux_req_burst),
 .aux_req_burst_data(unused_aux_req_burst_data),
 .aux_req_byte_enable(unused_aux_req_byte_enable),
 .aux_rsp_valid(aux_rsp_valid),
 .aux_rsp_ready(aux_rsp_ready),
 .aux_rsp_data(aux_rsp_data),
 .aux_rsp_error(aux_rsp_error),
 .aux_busy(unused_aux_busy),
 .aux_aborted(unused_aux_aborted),
 .lcd_req_valid(lcd_req_valid),
 .lcd_req_ready(lcd_req_ready),
 .lcd_req_addr(lcd_req_addr),
 .lcd_rsp_valid(lcd_rsp_valid),
 .lcd_rsp_ready(lcd_rsp_ready),
 .lcd_rsp_data(lcd_rsp_data),
 .lcd_rsp_last(lcd_rsp_last),
 .lcd_rsp_error(lcd_rsp_error),
 .lcd_busy(unused_lcd_busy),
 .cache_hits(unused_cache_hits),
 .cache_misses(unused_cache_misses),
 .completed_reads(unused_completed_reads),
 .completed_writes(unused_completed_writes),
 .p0_cache_hits(unused_p0_cache_hits),
 .p0_cache_misses(unused_p0_cache_misses),
 .p0_row_reads(unused_p0_row_reads),
 .p0_wait_cycles(unused_p0_wait_cycles),
 .p0_service_cycles(unused_p0_service_cycles),
 .p1_cache_hits(unused_p1_cache_hits),
 .p1_cache_misses(unused_p1_cache_misses),
 .p0_read_wait_cycles(unused_p0_read_wait_cycles),
 .p0_read_service_cycles(unused_p0_read_service_cycles),
 .sdram_a(sdram_a),
 .sdram_bs(sdram_bs),
 .sdram_cke(sdram_cke),
 .sdram_cs_n(sdram_cs_n),
 .sdram_dq(sdram_dq),
 .sdram_clk(sdram_clk),
 .sdram_ras_n(sdram_ras_n),
 .sdram_cas_n(sdram_cas_n),
 .sdram_we_n(sdram_we_n),
 .sdram_ldqm(sdram_ldqm),
 .sdram_udqm(sdram_udqm),
 .prefetch_req_valid(prefetch_req_valid),
 .prefetch_req_ready(prefetch_req_ready),
 .prefetch_req_address(prefetch_req_address),
 .prefetch_rsp_valid(prefetch_rsp_valid),
 .prefetch_rsp_ready(prefetch_rsp_ready),
 .prefetch_rsp_data(prefetch_rsp_data),
 .prefetch_req_generation,.prefetch_req_bank,.prefetch_req_plane,.prefetch_req_index,.prefetch_req_block,
 .prefetch_rsp_generation,.prefetch_rsp_bank,.prefetch_rsp_plane,.prefetch_rsp_index,.prefetch_rsp_block,
 .prefetch_rsp_error(prefetch_rsp_error),
 .prefetch_busy(prefetch_busy),
 .command_valid(command_valid),
 .command_write(command_write),
 .command_address(command_address),
 .command_client(command_client),
 .stream_candidate_wait_cycles(stream_candidate_wait_cycles),
 .stream_idle_candidate_wait_cycles(stream_idle_candidate_wait_cycles),
 .stream_write_accepts(stream_write_accepts),
 .idle(idle));
 cu72_sdram_model #(.T_AC_NS(TAC_NS)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 logic [31:0] stream_candidate_wait_cycles,stream_idle_candidate_wait_cycles,stream_write_accepts;
 logic overlap_write_finished=0;
 integer coincident_grants=0,coincident_responses=0;
 integer physical_prefetch=0,physical_write=0,physical_aux=0,physical_lcd=0,checks=0;
 always @(posedge clk)if(!rst)begin
  if(prefetch_rsp_valid&&prefetch_rsp_ready&&dut.p_valid&&dut.p_ready&&dut.p_write)coincident_grants<=coincident_grants+1;
  if(prefetch_rsp_valid&&prefetch_rsp_ready&&dut.t_rsp_valid&&dut.t_rsp_ready)coincident_responses<=coincident_responses+1;
  if(dut.snapshot_valid&&dut.snapshot_address!==prefetch_req_address)$fatal(1,"snapshot address mismatch");
  if(command_valid)begin
  if(command_address[2:0]!=0||command_address<24'h080000)$fatal(1,"unaligned physical command");
  case(command_client)
   0:if(command_write)physical_write<=physical_write+1;else $fatal(1,"disabled legacy read issued");
   1:physical_aux<=physical_aux+1;
   2:physical_lcd<=physical_lcd+1;
   3:begin if(command_write)$fatal(1,"prefetch wrote physical memory");physical_prefetch<=physical_prefetch+1;end
  endcase
  end
 end
 task automatic write_tile(input logic[1:0]bank,input logic[16:0]idx,input integer seed);
  begin
   @(negedge clk);write_generation=1;write_bank=bank;write_plane=0;write_index=idx;
   for(integer i=0;i<32;i=i+1)write_pixels[i*16+:16]=16'(seed+i);
   write_valid=1;do @(posedge clk);while(!write_ready);
   @(negedge clk);write_valid=0;
   while(!write_done_valid)@(negedge clk);
   if(write_done_error)$fatal(1,"tile write error");
   write_done_ready=1;@(posedge clk);@(negedge clk);write_done_ready=0;
  end
 endtask
 task automatic request(input logic[23:0]addr);
  logic [23:0] offset;
  begin
   @(negedge clk);prefetch_req_address=addr;prefetch_req_generation=prefetch_req_generation+1;
   prefetch_req_bank=addr>=24'h480000 ? 2'd1 : 2'd0;offset=addr-(addr>=24'h480000 ? 24'h480000 : 24'h080000);
   prefetch_req_plane=0;prefetch_req_index=17'(32'(offset)/32);prefetch_req_block=2'(32'(offset)/8);
   prefetch_req_valid=1;do @(posedge clk);while(!prefetch_req_ready);
   @(negedge clk);prefetch_req_valid=0;
   expected_generation=prefetch_req_generation;expected_bank=prefetch_req_bank;expected_plane=prefetch_req_plane;expected_index=prefetch_req_index;expected_block=prefetch_req_block;
  end
 endtask
 task automatic stream(input integer seed,input bit bad,input bit abort_edge);
  logic[127:0]saved;
  begin
   while(!prefetch_rsp_valid)@(negedge clk);saved=prefetch_rsp_data;
   if(prefetch_rsp_generation!==expected_generation||prefetch_rsp_bank!==expected_bank||prefetch_rsp_plane!==expected_plane||prefetch_rsp_index!==expected_index||prefetch_rsp_block!==expected_block||prefetch_rsp_error!=bad)$fatal(1,"wide block tag/error mismatch");
   for(integer i=0;i<8;i=i+1)if(!bad&&saved[i*16+:16]!==16'(seed+i))$fatal(1,"wide payload mismatch word%0d",i);
   repeat(16)begin
    @(negedge clk);
    if(!prefetch_busy||idle||!prefetch_rsp_valid||prefetch_rsp_data!==saved||prefetch_rsp_generation!==expected_generation||prefetch_rsp_bank!==expected_bank||prefetch_rsp_plane!==expected_plane||prefetch_rsp_index!==expected_index||prefetch_rsp_block!==expected_block||prefetch_req_ready)$fatal(1,"held wide block changed");
   end
   if(abort_edge)abort_i=1;
   prefetch_rsp_ready=1;@(posedge clk);@(negedge clk);prefetch_rsp_ready=0;checks=checks+8;
   abort_i=0;
  end
 endtask
 task automatic issue_write(input logic[16:0]idx,input integer seed);
  begin
   @(negedge clk);write_generation=1;write_bank=1;write_plane=0;write_index=idx;
   for(integer i=0;i<32;i=i+1)write_pixels[i*16+:16]=16'(seed+i);
   write_valid=1;do @(posedge clk);while(!write_ready);@(negedge clk);write_valid=0;
  end
 endtask
 task automatic finish_write;
  begin
   while(!write_done_valid)@(negedge clk);
   if(write_done_error)$fatal(1,"overlap tile write error");
   write_done_ready=1;@(posedge clk);@(negedge clk);write_done_ready=0;
  end
 endtask
 task automatic final_coincidence(input bit response_edge,input logic[23:0]addr,input integer seed,input logic[16:0]idx,input integer write_seed);
  begin
   if(seed<0||seed>65528)$fatal(1,"invalid stimulus seed");
   request(addr);while(!prefetch_rsp_valid)@(negedge clk);issue_write(idx,write_seed);
   if(response_edge)begin while(!(dut.t_rsp_valid&&dut.t_rsp_ready))@(negedge clk);end
   else begin while(!(dut.p_valid&&dut.p_ready&&dut.p_write))@(negedge clk);end
   if(!prefetch_busy||prefetch_rsp_error||prefetch_rsp_generation!==expected_generation||prefetch_rsp_bank!==expected_bank||prefetch_rsp_plane!==expected_plane||prefetch_rsp_index!==expected_index||prefetch_rsp_block!==expected_block)$fatal(1,"coincident wide identity changed");
   for(integer i=0;i<8;i=i+1)if(prefetch_rsp_data[i*16+:16]!==16'(seed+i))$fatal(1,"coincident wide payload changed word%0d",i);
   prefetch_rsp_ready=1;@(posedge clk);@(negedge clk);prefetch_rsp_ready=0;checks=checks+8;
   if(!response_edge&&!dut.p_owned)$fatal(1,"block accept cleared newly admitted write owner");
   finish_write();while(!idle)@(negedge clk);
  end
 endtask
 initial begin
  rst=1;repeat(5)@(negedge clk);rst=0;while(!idle)@(negedge clk);
  // Every reference byte enters the actual model via accepted controller writes.
  write_tile(0,0,32'h4000);write_tile(0,1,32'h5000);
  if(model.write_commands!=8||physical_write!=8)$fatal(1,"tile population physical write count");
  request(24'h080000);while(!prefetch_rsp_valid)@(negedge clk);
  // P0 ownership lasts through stream drain, while unrelated HUD/LCD clients
  // retain the exact frozen bridge arbitration behavior.
  fork
   begin write_tile(1,0,32'h6000);overlap_write_finished=1;end
   begin
    @(negedge clk);aux_req_addr=24'h080008;aux_req_valid=1;
    do @(posedge clk);while(!aux_req_ready);@(negedge clk);aux_req_valid=0;
    while(!aux_rsp_valid)@(negedge clk);
    if(aux_rsp_error||aux_rsp_data!==16'h4008||!prefetch_busy)$fatal(1,"HUD blocked or corrupted behind held prefetch");
    aux_rsp_ready=1;@(posedge clk);@(negedge clk);aux_rsp_ready=0;
    lcd_req_addr=24'h080010;lcd_req_valid=1;
    do @(posedge clk);while(!lcd_req_ready);@(negedge clk);lcd_req_valid=0;
    for(integer i=0;i<8;i=i+1)begin
     while(!lcd_rsp_valid)@(negedge clk);
     if(lcd_rsp_error||lcd_rsp_data!==16'(32'h4010+i)||lcd_rsp_last!=(i==7)||!prefetch_busy)$fatal(1,"LCD blocked or corrupted behind held prefetch");
     lcd_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;
    end
    // A caller cannot overwrite the held raw snapshot with another request.
    prefetch_req_address=24'h080020;prefetch_req_valid=1;
    repeat(16)begin @(negedge clk);if(prefetch_req_ready)$fatal(1,"second raw read accepted during held stream");end
    prefetch_req_valid=0;
    begin
     while(!overlap_write_finished)@(negedge clk);
     if(!prefetch_busy||!prefetch_rsp_valid||prefetch_rsp_data[15:0]!==16'h4000)$fatal(1,"write completion changed held snapshot");
    end
    stream(32'h4000,0,0);
   end
  join
  request(24'h080020);stream(32'h5000,0,1);
  while(!idle)@(negedge clk);
  request(24'h000000);stream(0,1,0);
  while(!idle)@(negedge clk);
  final_coincidence(0,24'h080008,32'h4008,17'd1,32'h6100);
  final_coincidence(1,24'h080010,32'h4010,17'd2,32'h6200);
  // Match the real system abort contract: the receiver cancels its epoch,
  // while memory.abort_i stays low so an admitted write completes physically.
  request(24'h080018);while(!prefetch_rsp_valid)@(negedge clk);
  issue_write(17'd3,32'h6300);
  while(!(command_valid&&command_write&&command_client==0))@(negedge clk);
  if(idle||!tile_busy||!prefetch_busy)$fatal(1,"abort-drain ownership missing");
  fork
   begin finish_write();end
   begin stream(32'h4018,0,0);end
  join
  while(!idle)@(negedge clk);
  // Read every candidate byte through the same physical controller path.
  for(integer idx=0;idx<4;idx=idx+1)begin
   for(integer block_no=0;block_no<4;block_no=block_no+1)begin
    request(24'h480000+24'(idx*32+block_no*8));stream(32'h6000+idx*256+block_no*8,0,0);
   end
  end
  while(!idle)@(negedge clk);
  if(physical_prefetch!=21||physical_aux!=1||physical_lcd!=1||physical_write!=24||model.reads!=23||model.write_commands!=24)$fatal(1,"physical trace/accounting mismatch pref%0d write%0d reads%0d writes%0d",physical_prefetch,physical_write,model.reads,model.write_commands);
  if(stream_candidate_wait_cycles==0||stream_idle_candidate_wait_cycles==0)$fatal(1,"missing stream/write wait observation");
  if(stream_write_accepts<7||coincident_grants!=1||coincident_responses!=1)$fatal(1,"directed wide overlap coverage accepts%0d grants%0d responses%0d",stream_write_accepts,coincident_grants,coincident_responses);
  if(tile_busy||tile_aborted)$fatal(1,"tile adapter not drained");
  $display("WIDE_MEMORY_V81_PASS tac=%0.1f checks=%0d physical_prefetch=%0d physical_aux=%0d physical_lcd=%0d physical_write=%0d raw_abort_drains=1 invalid_address_no_command=1 held_stream_stable=1 actual_sdram_model=1",TAC_NS,checks,physical_prefetch,physical_aux,physical_lcd,physical_write);
  $display("OVERLAP_COUNTERS candidate_wait=%0d idle_candidate_wait=%0d write_accepts=%0d coincident_grants=%0d coincident_responses=%0d",stream_candidate_wait_cycles,stream_idle_candidate_wait_cycles,stream_write_accepts,coincident_grants,coincident_responses);
  $display("MODEL_LAST_WRITE address=%h data=%h",model.last_write_address,model.last_write_data);
  $finish;
 end
 initial begin #1000000;$fatal(1,"bounded memory test watchdog");end
endmodule
