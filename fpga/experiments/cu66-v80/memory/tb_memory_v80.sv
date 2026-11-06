`timescale 1ns/1ps
module tb_memory_v80 #(parameter real TAC_NS=2.0);
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
 logic [15:0] prefetch_rsp_data;
 logic [2:0] prefetch_rsp_beat;
 logic  prefetch_rsp_last;
 logic  prefetch_rsp_error;
 logic  prefetch_busy;
 logic  command_valid;
 logic  command_write;
 logic [23:0] command_address;
 logic [1:0] command_client;
 logic  idle;
 always #5 clk=~clk;
 always @(clk)read_clk<=#2.75 ~clk;
 cu80_memory_system #(.POWERUP_CYCLES(20)) dut(
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
 .prefetch_rsp_beat(prefetch_rsp_beat),
 .prefetch_rsp_last(prefetch_rsp_last),
 .prefetch_rsp_error(prefetch_rsp_error),
 .prefetch_busy(prefetch_busy),
 .command_valid(command_valid),
 .command_write(command_write),
 .command_address(command_address),
 .command_client(command_client),
 .idle(idle));
 cu72_sdram_model #(.T_AC_NS(TAC_NS)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 integer physical_prefetch=0,physical_write=0,physical_aux=0,physical_lcd=0,checks=0;
 always @(posedge clk)if(!rst&&command_valid)begin
  if(command_address[2:0]!=0||command_address<24'h080000)$fatal(1,"unaligned physical command");
  case(command_client)
   0:if(command_write)physical_write<=physical_write+1;else $fatal(1,"disabled legacy read issued");
   1:physical_aux<=physical_aux+1;
   2:physical_lcd<=physical_lcd+1;
   3:begin if(command_write)$fatal(1,"prefetch wrote physical memory");physical_prefetch<=physical_prefetch+1;end
  endcase
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
  begin
   @(negedge clk);prefetch_req_address=addr;prefetch_req_valid=1;
   do @(posedge clk);while(!prefetch_req_ready);
   @(negedge clk);prefetch_req_valid=0;
  end
 endtask
 task automatic stream(input integer seed,input bit bad,input bit abort_middle);
  logic[15:0]saved;
  begin
   for(integer i=0;i<8;i=i+1)begin
    while(!prefetch_rsp_valid)@(negedge clk);
    saved=prefetch_rsp_data;
    if(prefetch_rsp_beat!=3'(i)||prefetch_rsp_last!=(i==7)||prefetch_rsp_error!=bad||(!bad&&saved!==16'(seed+i)))$fatal(1,"raw BL8 beat mismatch beat%0d got%h seed%h",i,saved,seed);
    repeat(4)begin
     @(negedge clk);
     if(!prefetch_busy||idle||!prefetch_rsp_valid||prefetch_rsp_data!==saved||prefetch_rsp_beat!=3'(i)||prefetch_req_ready)$fatal(1,"raw BL8 held state changed");
    end
    if(abort_middle&&i==3)abort_i=1;
    prefetch_rsp_ready=1;@(posedge clk);@(negedge clk);prefetch_rsp_ready=0;checks=checks+1;
   end
   abort_i=0;
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
   begin write_tile(1,0,32'h6000);end
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
    stream(32'h4000,0,0);
   end
  join
  request(24'h080020);stream(32'h5000,0,1);
  while(!idle)@(negedge clk);
  request(24'h000000);stream(0,1,0);
  while(!idle)@(negedge clk);
  if(physical_prefetch!=2||physical_aux!=1||physical_lcd!=1||physical_write!=12||model.reads!=4||model.write_commands!=12)$fatal(1,"physical trace/accounting mismatch");
  if(tile_busy||tile_aborted)$fatal(1,"tile adapter not drained");
  $display("MEMORY_V80_PASS tac=%0.1f checks=%0d physical_prefetch=%0d physical_aux=%0d physical_lcd=%0d physical_write=%0d raw_abort_drains=1 invalid_address_no_command=1 held_stream_stable=1 actual_sdram_model=1",TAC_NS,checks,physical_prefetch,physical_aux,physical_lcd,physical_write);
  $display("MODEL_LAST_WRITE address=%h data=%h",model.last_write_address,model.last_write_data);
  $finish;
 end
 initial begin #1000000;$fatal(1,"bounded memory test watchdog");end
endmodule
