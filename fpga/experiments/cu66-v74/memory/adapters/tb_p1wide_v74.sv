`timescale 1ns/1ps
module tb_p1wide_v74 #(parameter real TAC_NS=2.0);
 logic clk=0,read_clk=0,rst=1;
 always #5 clk=~clk;
 always @(clk)read_clk<=#2.75 ~clk;
 logic[1:0] valid=0,ready,writing=0,burst=0,rsp_valid,rsp_ready=0,rsp_error;
 logic[23:0]addr[0:1];logic[15:0]data[0:1],byte_enable[0:1],rsp_data[0:1];logic[127:0]burst_data[0:1];
 logic mem_req_valid,mem_req_ready,mem_req_write,mem_rsp_valid,mem_idle;
 logic[23:0]mem_req_addr;logic[127:0]mem_req_burst_data;logic[15:0]mem_req_byte_enable,mem_rsp_data;
 logic lcd_req_ready,lcd_rsp_valid,lcd_rsp_last,lcd_rsp_error,lcd_busy,bridge_busy;logic[15:0]lcd_rsp_data;
 logic[31:0]cache_hits,cache_misses,completed_reads,completed_writes;
 logic p1_read_burst=0;logic[127:0]p1_rsp_burst_data;
 logic p0_read_burst=0;logic[127:0]p0_rsp_burst_data;
 logic[31:0]p0_cache_hits,p0_cache_misses,p0_row_reads,p0_wait_cycles,p0_service_cycles,p1_cache_hits,p1_cache_misses,p0_read_wait_cycles,p0_read_service_cycles;
 wire[12:0]sdram_a;wire[1:0]sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 cu74_word_bridge dut(.clk,.rst,.p0_read_burst,.p0_rsp_burst_data,.p1_read_burst,.p1_rsp_burst_data,
  .p0_valid(valid[0]),.p0_ready(ready[0]),.p0_write(writing[0]),.p0_addr(addr[0]),.p0_data(data[0]),.p0_burst(burst[0]),.p0_burst_data(burst_data[0]),.p0_byte_enable(byte_enable[0]),.p0_rsp_valid(rsp_valid[0]),.p0_rsp_ready(rsp_ready[0]),.p0_rsp_data(rsp_data[0]),.p0_rsp_error(rsp_error[0]),
  .p1_valid(valid[1]),.p1_ready(ready[1]),.p1_write(writing[1]),.p1_addr(addr[1]),.p1_data(data[1]),.p1_burst(burst[1]),.p1_burst_data(burst_data[1]),.p1_byte_enable(byte_enable[1]),.p1_rsp_valid(rsp_valid[1]),.p1_rsp_ready(rsp_ready[1]),.p1_rsp_data(rsp_data[1]),.p1_rsp_error(rsp_error[1]),
  .lcd_req_valid(1'b0),.lcd_req_ready,.lcd_req_addr(24'd0),.lcd_rsp_valid,.lcd_rsp_ready(1'b0),.lcd_rsp_data,.lcd_rsp_last,.lcd_rsp_error,.lcd_busy,
  .mem_req_valid,.mem_req_ready,.mem_req_write,.mem_req_addr,.mem_req_burst_data,.mem_req_byte_enable,.mem_rsp_valid,.mem_rsp_data,.mem_idle,.bridge_busy,.cache_hits,.cache_misses,.completed_reads,.completed_writes,.p0_cache_hits,.p0_cache_misses,.p0_row_reads,.p0_wait_cycles,.p0_service_cycles,.p1_cache_hits,.p1_cache_misses,.p0_read_wait_cycles,.p0_read_service_cycles);
 cu72_sdram_controller #(.POWERUP_CYCLES(20)) controller(.clk,.read_clk,.reset(rst),.request_valid(mem_req_valid),.request_ready(mem_req_ready),.request_write(mem_req_write),.request_address(mem_req_addr),.request_burst_data(mem_req_burst_data),.request_byte_enable(mem_req_byte_enable),.response_valid(mem_rsp_valid),.response_data(mem_rsp_data),.idle(mem_idle),.sdram_a,.sdram_bs,.sdram_cke,.sdram_cs_n,.sdram_dq,.sdram_clk,.sdram_ras_n,.sdram_cas_n,.sdram_we_n,.sdram_ldqm,.sdram_udqm);
 cu72_sdram_model #(.T_AC_NS(TAC_NS)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 `include "cu70_memory_map.svh"
 integer checks=0,reads_before=0,writes_before=0,cycles=0;logic[127:0]payload;logic[15:0]value;
 always @(posedge clk)cycles=cycles+1;
 task automatic op(input bit port_id,wr,wide,wide_read,input logic[23:0]a,input logic[127:0]payload_i,input logic[15:0]mask,input bit bad,output logic[15:0]result);
  logic[15:0]saved;logic[127:0]saved_line;
  begin
   @(negedge clk);valid[port_id]=1;writing[port_id]=wr;burst[port_id]=wide;addr[port_id]=a;data[port_id]=payload_i[15:0];burst_data[port_id]=payload_i;byte_enable[port_id]=mask;p1_read_burst=wide_read;
   do @(posedge clk);while(!ready[port_id]);
   @(negedge clk);valid[port_id]=0;p1_read_burst=0;writing[port_id]=0;burst[port_id]=0;addr[port_id]=0;data[port_id]=0;burst_data[port_id]=0;byte_enable[port_id]=0;
   while(!rsp_valid[port_id])@(negedge clk);
   saved=rsp_data[port_id];saved_line=p1_rsp_burst_data;
   if(wide_read&&!bad&&(saved_line!==payload_i||saved!==payload_i[15:0]))$fatal(1,"P1 full snapshot mismatch got%h expected%h",saved_line,payload_i);
   if(wide_read&&bad&&saved_line!==0)$fatal(1,"rejected P1 payload was not zero");if(rsp_error[port_id]!==bad)$fatal(1,"cache operation error");
   repeat(8)begin @(negedge clk);if(!bridge_busy||!rsp_valid[port_id]||rsp_data[port_id]!==saved||rsp_error[port_id]!==bad||p1_rsp_burst_data!==saved_line)$fatal(1,"held wide/scalar cache response changed");end
   rsp_ready[port_id]=1;@(posedge clk);@(negedge clk);rsp_ready[port_id]=0;result=saved;checks=checks+1;
  end
 endtask
 initial begin
  for(integer i=0;i<2;i=i+1)begin addr[i]=0;data[i]=0;burst_data[i]=0;byte_enable[i]=0;end
  repeat(5)@(negedge clk);rst=0;while(!mem_idle)@(negedge clk);
  for(integer i=0;i<8;i=i+1)payload[i*16+:16]=16'(32'ha000+i);
  op(1,1,1,0,DIAGNOSTIC_BASE,payload,16'hffff,0,value);
  op(0,0,0,0,DIAGNOSTIC_BASE+3,0,0,0,value);if(value!==16'ha003)$fatal(1,"prime p0");
  op(1,0,0,0,DIAGNOSTIC_BASE+3,0,0,0,value);if(value!==16'ha003)$fatal(1,"prime p1");
  reads_before=model.reads;
  op(0,0,0,0,DIAGNOSTIC_BASE+4,0,0,0,value);op(1,0,0,0,DIAGNOSTIC_BASE+4,0,0,0,value);
  if(model.reads!=reads_before)$fatal(1,"primed scalar caches missed");
  payload=0;payload[3*16+:16]=16'h55aa;
  op(1,1,1,0,DIAGNOSTIC_BASE,payload,16'h0040,0,value);
  reads_before=model.reads;
  op(0,0,0,0,DIAGNOSTIC_BASE+3,0,0,0,value);if(value!==16'ha0aa)$fatal(1,"p1 partial write failed p0 cache invalidation");
  op(1,0,0,0,DIAGNOSTIC_BASE+3,0,0,0,value);if(value!==16'ha0aa)$fatal(1,"p1 partial write failed own cache invalidation");
  if(model.reads!=reads_before+2)$fatal(1,"masked write did not invalidate both caches");
  payload=0;payload[4*16+:16]=16'hbb66;
  op(0,1,1,0,DIAGNOSTIC_BASE,payload,16'h0200,0,value);
  op(1,0,0,0,DIAGNOSTIC_BASE+4,0,0,0,value);if(value!==16'hbb04)$fatal(1,"p0 highbyte write failed p1 invalidation");
  op(0,0,0,0,DIAGNOSTIC_BASE+4,0,0,0,value);if(value!==16'hbb04)$fatal(1,"p0 highbyte write failed own invalidation");
  op(0,1,0,0,DIAGNOSTIC_BASE+5,128'hc123,0,0,value);
  op(1,0,0,0,DIAGNOSTIC_BASE+5,0,0,0,value);if(value!==16'hc123)$fatal(1,"scalar fallback payload/mask");
  op(0,0,0,0,DIAGNOSTIC_BASE+6,0,0,0,value);if(value!==16'ha006)$fatal(1,"scalar fallback damaged neighbor");
  writes_before=model.write_commands;
  op(0,1,1,0,DIAGNOSTIC_BASE+1,0,16'hffff,1,value);
  op(1,1,1,0,DIAGNOSTIC_BASE,0,0,1,value);
  op(0,0,1,0,DIAGNOSTIC_BASE,0,16'hffff,1,value);
  op(1,1,1,0,0,0,16'hffff,1,value);
  if(model.write_commands!=writes_before)$fatal(1,"invalid wide reached controller");
  // Miss then hit wide128 reads must collect/snapshot every beat, including #7.
  for(integer i=0;i<8;i=i+1)payload[i*16+:16]=16'(32'hd120+i*77);
  op(0,1,1,0,DIAGNOSTIC_BASE+256,payload,16'hffff,0,value);
  reads_before=model.reads;
  op(1,0,0,1,DIAGNOSTIC_BASE+256,payload,0,0,value);
  if(model.reads!=reads_before+1)$fatal(1,"wide P1 miss did not issue exactly one BL8");
  reads_before=model.reads;
  op(1,0,0,1,DIAGNOSTIC_BASE+256,payload,0,0,value);
  if(model.reads!=reads_before)$fatal(1,"wide P1 hit reached SDRAM");
  // A physical P0 alias invalidates the complete P1 cache line.
  op(0,1,0,0,DIAGNOSTIC_BASE+263,128'habcd,0,0,value);
  payload[127:112]=16'habcd;reads_before=model.reads;
  op(1,0,0,1,DIAGNOSTIC_BASE+256,payload,0,0,value);
  if(model.reads!=reads_before+1)$fatal(1,"wide P1 alias failed invalidation");
  reads_before=model.reads;writes_before=model.write_commands;
  op(1,0,0,1,DIAGNOSTIC_BASE+260,0,0,1,value);
  op(1,0,0,1,DIAGNOSTIC_BASE+257,0,0,1,value);
  op(1,0,0,1,CANONICAL0_BASE+24'(CANONICAL0_WORDS),0,0,1,value);
  op(1,0,0,1,0,0,0,1,value);
  op(1,1,0,1,DIAGNOSTIC_BASE+256,0,0,1,value);
  op(1,0,1,1,DIAGNOSTIC_BASE+256,0,16'hffff,1,value);
  op(1,1,1,1,DIAGNOSTIC_BASE+256,0,16'hffff,1,value);
  if(model.reads!=reads_before||model.write_commands!=writes_before)$fatal(1,"bad wide P1 issued SDRAM command");
  // Flush a held response, both caches and the controller. Stored data persists.
  @(negedge clk);valid[0]=1;addr[0]=DIAGNOSTIC_BASE+3;
  do @(posedge clk);while(!ready[0]);@(negedge clk);valid[0]=0;
  while(!rsp_valid[0])@(negedge clk);
  rst=1;repeat(5)begin @(negedge clk);if(rsp_valid!=0||bridge_busy)$fatal(1,"reset retained cached response");end
  rst=0;while(!mem_idle)@(negedge clk);repeat(5)@(negedge clk);
  op(0,0,0,0,DIAGNOSTIC_BASE+3,0,0,0,value);if(value!==16'ha0aa||cache_misses!=1)$fatal(1,"fresh scalar cache after reset");
  if(p1_rsp_burst_data!==p0_rsp_burst_data)$fatal(1,"shared burst snapshot mismatch");
  if(lcd_busy||lcd_rsp_valid||lcd_rsp_last||lcd_rsp_error||lcd_rsp_data!=0||lcd_req_ready)$fatal(1,"inactive LCD port activity");
  for(integer i=0;i<8;i=i+1)if(p0_rsp_burst_data[i*16+:16]!==model.mem[DIAGNOSTIC_BASE+24'(i)])$fatal(1,"full cached snapshot mismatch");
  if(p0_rsp_burst_data[63:48]!==16'ha0aa||p0_cache_hits+p1_cache_hits!=cache_hits||p0_cache_misses+p1_cache_misses!=cache_misses||p0_row_reads!=0||p0_read_wait_cycles>p0_wait_cycles||p0_read_service_cycles>p0_service_cycles)$fatal(1,"cache profile or wide snapshot");
  $display("MEMORY_V74_P1WIDE_PASS checks=%0d cycles=%0d cache_hits=%0d cache_misses=%0d active_words=%0d reads=%0d write_commands=%0d completed_reads=%0d completed_writes=%0d trace_address=%0d trace_data=%0d bus_beats=%0d ACT=%0d PRE=%0d REF=%0d MRS=%0d",checks,cycles,cache_hits,cache_misses,model.writes,model.reads,model.write_commands,completed_reads,completed_writes,model.last_write_address,model.last_write_data,model.write_bus_beats,model.acts,model.pres,model.refreshes,model.mrs);
  $finish;
 end
 initial begin #10000000;$fatal(1,"cache test watchdog");end
endmodule
