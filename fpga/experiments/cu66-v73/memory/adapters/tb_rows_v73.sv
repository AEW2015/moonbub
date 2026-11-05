`timescale 1ns/1ps
module tb_rows_v73 #(parameter real TAC_NS=2.0,parameter integer CACHE_LINES=8);
 logic clk=0,read_clk=0,rst=1;
 always #5 clk=~clk;
 always @(clk)read_clk<=#2.75 ~clk;
 logic[1:0] valid=0,ready,writing=0,burst=0,rsp_valid,rsp_ready=0,rsp_error;
 logic p0_read_burst=0;logic[127:0]p0_rsp_burst_data;
 logic[23:0]addr[0:1];logic[15:0]data[0:1],byte_enable[0:1],rsp_data[0:1];logic[127:0]burst_data[0:1];
 logic mem_req_valid,mem_req_ready,mem_req_write,mem_rsp_valid,mem_idle;
 logic[23:0]mem_req_addr;logic[127:0]mem_req_burst_data;logic[15:0]mem_req_byte_enable,mem_rsp_data;
 logic lcd_req_ready,lcd_rsp_valid,lcd_rsp_last,lcd_rsp_error,lcd_busy,bridge_busy;logic[15:0]lcd_rsp_data;
 logic[31:0]cache_hits,cache_misses,completed_reads,completed_writes;
 logic[31:0]p0_cache_hits,p0_cache_misses,p0_row_reads,p0_wait_cycles,p0_service_cycles,p1_cache_hits,p1_cache_misses,p0_read_wait_cycles,p0_read_service_cycles;
 wire[12:0]sdram_a;wire[1:0]sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 cu73_word_bridge #(.P0_CACHE_LINES(CACHE_LINES)) dut(.clk,.rst,.p0_read_burst,.p0_rsp_burst_data,
  .p0_valid(valid[0]),.p0_ready(ready[0]),.p0_write(writing[0]),.p0_addr(addr[0]),.p0_data(data[0]),.p0_burst(burst[0]),.p0_burst_data(burst_data[0]),.p0_byte_enable(byte_enable[0]),.p0_rsp_valid(rsp_valid[0]),.p0_rsp_ready(rsp_ready[0]),.p0_rsp_data(rsp_data[0]),.p0_rsp_error(rsp_error[0]),
  .p1_valid(valid[1]),.p1_ready(ready[1]),.p1_write(writing[1]),.p1_addr(addr[1]),.p1_data(data[1]),.p1_burst(burst[1]),.p1_burst_data(burst_data[1]),.p1_byte_enable(byte_enable[1]),.p1_rsp_valid(rsp_valid[1]),.p1_rsp_ready(rsp_ready[1]),.p1_rsp_data(rsp_data[1]),.p1_rsp_error(rsp_error[1]),
  .lcd_req_valid(1'b0),.lcd_req_ready,.lcd_req_addr(24'd0),.lcd_rsp_valid,.lcd_rsp_ready(1'b0),.lcd_rsp_data,.lcd_rsp_last,.lcd_rsp_error,.lcd_busy,
  .mem_req_valid,.mem_req_ready,.mem_req_write,.mem_req_addr,.mem_req_burst_data,.mem_req_byte_enable,.mem_rsp_valid,.mem_rsp_data,.mem_idle,.bridge_busy,.cache_hits,.cache_misses,.completed_reads,.completed_writes,
  .p0_cache_hits,.p0_cache_misses,.p0_row_reads,.p0_wait_cycles,.p0_service_cycles,.p1_cache_hits,.p1_cache_misses,.p0_read_wait_cycles,.p0_read_service_cycles);
 cu72_sdram_controller #(.POWERUP_CYCLES(20)) controller(.clk,.read_clk,.reset(rst),.request_valid(mem_req_valid),.request_ready(mem_req_ready),.request_write(mem_req_write),.request_address(mem_req_addr),.request_burst_data(mem_req_burst_data),.request_byte_enable(mem_req_byte_enable),.response_valid(mem_rsp_valid),.response_data(mem_rsp_data),.idle(mem_idle),.sdram_a,.sdram_bs,.sdram_cke,.sdram_cs_n,.sdram_dq,.sdram_clk,.sdram_ras_n,.sdram_cas_n,.sdram_we_n,.sdram_ldqm,.sdram_udqm);
 cu72_sdram_model #(.T_AC_NS(TAC_NS)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 `include "cu70_memory_map.svh"
 integer cycles=0,checks=0,wide_reads=0,second_tile_misses=0,first_tile_misses=0,saved_reads=0,saved_writes=0,first_start=0,first_cycles=0,second_start=0,second_cycles=0,chroma_first_misses=0,chroma_second_misses=0,row_address=0;
 logic[127:0]expected[0:8],chroma_first[0:7],chroma_second[0:7];logic[127:0]payload;logic[15:0]got;
 always @(posedge clk)cycles=cycles+1;
 task automatic op(input bit port_id,wr,wide,wide_read,input logic[23:0]a,input logic[127:0]payload_i,input logic[15:0]mask,input bit bad,output logic[15:0]result);
  logic[15:0]saved;logic[127:0]saved_line;
  begin
   @(negedge clk);valid[port_id]=1;writing[port_id]=wr;burst[port_id]=wide;addr[port_id]=a;data[port_id]=payload_i[15:0];burst_data[port_id]=payload_i;byte_enable[port_id]=mask;p0_read_burst=wide_read;
   do @(posedge clk);while(!ready[port_id]);
   @(negedge clk);valid[port_id]=0;writing[port_id]=0;burst[port_id]=0;p0_read_burst=0;addr[port_id]=0;data[port_id]=0;burst_data[port_id]=0;byte_enable[port_id]=0;
   while(!rsp_valid[port_id])@(negedge clk);
   saved=rsp_data[port_id];saved_line=p0_rsp_burst_data;
   if(rsp_error[port_id]!==bad)$fatal(1,"row error mismatch");
   if(wide_read&&!bad&&saved_line!==payload_i)$fatal(1,"wide row data mismatch addr%h got%h expected%h",a,saved_line,payload_i);
   if(wide_read&&!bad&&saved!==payload_i[a[2:0]*16+:16])$fatal(1,"selected scalar inconsistent with wide row");
   if(wide_read&&bad&&saved_line!==0)$fatal(1,"bad read exposed wide payload");
   repeat(32)begin
    @(negedge clk);
    if(!bridge_busy||!rsp_valid[port_id]||rsp_data[port_id]!==saved||rsp_error[port_id]!==bad||(port_id==0&&p0_rsp_burst_data!==saved_line))$fatal(1,"held wide/scalar response changed");
   end
   rsp_ready[port_id]=1;@(posedge clk);@(negedge clk);rsp_ready[port_id]=0;result=saved;checks=checks+1;
   if(wide_read)wide_reads=wide_reads+1;
  end
 endtask
 initial begin
  for(integer i=0;i<2;i=i+1)begin addr[i]=0;data[i]=0;burst_data[i]=0;byte_enable[i]=0;end
  repeat(5)@(negedge clk);rst=0;while(!mem_idle)@(negedge clk);
  // Populate every word through actual controller writes, not a model backdoor.
  for(integer row=0;row<9;row=row+1)begin
   for(integer word_no=0;word_no<8;word_no=word_no+1)expected[row][word_no*16+:16]=16'(32'h8000+row*256+word_no);
   op(1,1,1,0,CANONICAL0_BASE+24'(row*360),expected[row],16'hffff,0,got);
  end
  saved_reads=model.reads;first_start=cycles;
  for(integer row=0;row<8;row=row+1)op(0,0,0,1,CANONICAL0_BASE+24'(row*360),expected[row],0,0,got);
  first_tile_misses=model.reads-saved_reads;first_cycles=cycles-first_start;
  if(first_tile_misses!=8)$fatal(1,"first tile did not fill eight row lines");
  saved_reads=model.reads;second_start=cycles;
  for(integer row=0;row<8;row=row+1)op(0,0,0,1,CANONICAL0_BASE+24'(row*360)+24'd4,expected[row],0,0,got);
  second_tile_misses=model.reads-saved_reads;second_cycles=cycles-second_start;
  if(second_tile_misses!=(CACHE_LINES==8?0:8))$fatal(1,"adjacent tile row cache reuse mismatch");
  // Ninth row evicts exactly the oldest row in an eight-entry RR working set.
  op(0,0,0,1,CANONICAL0_BASE+24'd2880,expected[8],0,0,got);
  saved_reads=model.reads;op(0,0,0,1,CANONICAL0_BASE+24'd360,expected[1],0,0,got);
  if(model.reads-saved_reads!=(CACHE_LINES==8?0:1))$fatal(1,"unrelated row evicted unexpectedly");
  saved_reads=model.reads;op(0,0,0,1,CANONICAL0_BASE,expected[0],0,0,got);
  if(model.reads!=saved_reads+1)$fatal(1,"oldest row was not evicted");
  // Both write clients invalidate the complete returned row, including partial bytes.
  op(1,0,0,0,CANONICAL0_BASE+3,0,0,0,got);
  payload=0;payload[3*16+:16]=16'h00aa;op(1,1,1,0,CANONICAL0_BASE,payload,16'h0040,0,got);
  expected[0][3*16+:8]=8'haa;saved_reads=model.reads;
  op(0,0,0,1,CANONICAL0_BASE+4,expected[0],0,0,got);op(1,0,0,0,CANONICAL0_BASE+3,0,0,0,got);
  if(model.reads!=saved_reads+2||got!==16'h80aa)$fatal(1,"p1 masked write missed p0/p1 invalidation");
  payload=0;payload[4*16+:16]=16'hbb00;op(0,1,1,0,CANONICAL0_BASE,payload,16'h0200,0,got);
  expected[0][4*16+8+:8]=8'hbb;saved_reads=model.reads;
  op(0,0,0,1,CANONICAL0_BASE,expected[0],0,0,got);op(1,0,0,0,CANONICAL0_BASE+4,0,0,0,got);
  if(model.reads!=saved_reads+2||got!==16'hbb04)$fatal(1,"p0 masked write missed p0/p1 invalidation");
  saved_reads=model.reads;saved_writes=model.write_commands;
  op(0,1,0,1,CANONICAL0_BASE,0,0,1,got);
  op(0,0,1,1,CANONICAL0_BASE,0,16'hffff,1,got);
  op(0,0,0,1,CANONICAL0_BASE+2,0,0,1,got);
  op(0,0,0,1,0,0,0,1,got);
  if(model.reads!=saved_reads||model.write_commands!=saved_writes)$fatal(1,"invalid wide-read reached SDRAM");
  // Chroma pitch180 alternates lower/upper halves; adjacent tiles reuse four
  // of the eight aligned rows rather than all eight luma row blocks.
  for(integer row=0;row<8;row=row+1)begin
   for(integer word_no=0;word_no<8;word_no=word_no+1)begin
    chroma_first[row][word_no*16+:16]=16'(32'h4000+row*64+word_no);
    chroma_second[row][word_no*16+:16]=16'(32'h5000+row*64+word_no);
   end
   row_address=int'(CANONICAL0_BASE)+172800+row*180;
   op(1,1,1,0,24'(row_address)&24'hfffff8,chroma_first[row],16'hffff,0,got);
   if(row_address%8==4)op(1,1,1,0,(24'(row_address)&24'hfffff8)+24'd8,chroma_second[row],16'hffff,0,got);
   else chroma_second[row]=chroma_first[row];
  end
  saved_reads=model.reads;
  for(integer row=0;row<8;row=row+1)op(0,0,0,1,CANONICAL0_BASE+24'd172800+24'(row*180),chroma_first[row],0,0,got);
  chroma_first_misses=model.reads-saved_reads;
  saved_reads=model.reads;
  for(integer row=0;row<8;row=row+1)op(0,0,0,1,CANONICAL0_BASE+24'd172804+24'(row*180),chroma_second[row],0,0,got);
  chroma_second_misses=model.reads-saved_reads;
  if(chroma_first_misses!=8||chroma_second_misses!=(CACHE_LINES==8?4:8))$fatal(1,"adjacent chroma half-row cache reuse mismatch");
  // Coordinated reset suppresses a held wide snapshot; subsequent reads miss fresh.
  @(negedge clk);valid[0]=1;addr[0]=CANONICAL0_BASE;p0_read_burst=1;
  do @(posedge clk);while(!ready[0]);@(negedge clk);valid[0]=0;p0_read_burst=0;
  while(!rsp_valid[0])@(negedge clk);
  repeat(32)@(negedge clk);rst=1;
  repeat(5)begin @(negedge clk);if(rsp_valid!=0||bridge_busy)$fatal(1,"reset retained wide response");end
  rst=0;while(!mem_idle)@(negedge clk);repeat(5)@(negedge clk);
  op(0,0,0,1,CANONICAL0_BASE,expected[0],0,0,got);
  if(p0_cache_misses!=1||p0_row_reads!=1||p0_cache_hits!=0||p0_read_service_cycles==0||p0_read_wait_cycles>p0_wait_cycles||p0_read_service_cycles>p0_service_cycles)$fatal(1,"wide profile reset/accounting");
  if(cache_hits!=p0_cache_hits+p1_cache_hits||cache_misses!=p0_cache_misses+p1_cache_misses)$fatal(1,"per-client profile sum");
  if(lcd_busy||lcd_rsp_valid||lcd_rsp_last||lcd_rsp_error||lcd_rsp_data!=0||lcd_req_ready)$fatal(1,"inactive LCD port activity");
  $display("MEMORY_V73_ROWS_PASS cache_lines=%0d checks=%0d wide_reads=%0d first_tile_misses=%0d second_tile_misses=%0d chroma_first_misses=%0d chroma_second_misses=%0d first_cycles=%0d second_cycles=%0d cycles=%0d p0_hits=%0d p0_misses=%0d p0_rows=%0d p0_wait=%0d p0_service=%0d read_wait=%0d read_service=%0d active_words=%0d reads=%0d write_commands=%0d completed_reads=%0d completed_writes=%0d trace_address=%0d trace_data=%0d bus_beats=%0d ACT=%0d PRE=%0d REF=%0d MRS=%0d",CACHE_LINES,checks,wide_reads,first_tile_misses,second_tile_misses,chroma_first_misses,chroma_second_misses,first_cycles,second_cycles,cycles,p0_cache_hits,p0_cache_misses,p0_row_reads,p0_wait_cycles,p0_service_cycles,p0_read_wait_cycles,p0_read_service_cycles,model.writes,model.reads,model.write_commands,completed_reads,completed_writes,model.last_write_address,model.last_write_data,model.write_bus_beats,model.acts,model.pres,model.refreshes,model.mrs);
  $finish;
 end
 initial begin #10000000;$fatal(1,"wide row test watchdog");end
endmodule
