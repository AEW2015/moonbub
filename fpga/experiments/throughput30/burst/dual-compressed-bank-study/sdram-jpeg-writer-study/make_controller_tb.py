#!/usr/bin/env python3
"""Adapt the pinned writer test to the actual experimental SDRAM controller."""
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
changes=[
 ('integer cycle=0,busy=0,req_count=0;reg[127:0] memory[0:MAX_BURSTS-1];',
  'integer cycle=0,req_count=0;wire busy=!mem_idle;'),
 ('wire write_ready=!force_stall&&(busy==0)&&(cycle%5!=0);wire write_drain_done=(busy==0);',
  '''wire write_ready,controller_ready,write_drain_done,mem_idle;assign write_drain_done=mem_idle;
  assign write_ready=controller_ready&&!force_stall;
  wire read_clk;assign #2.75 read_clk=~clk;
  wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq,rdata;wire sclk,ras,cas,we,ldqm,udqm,rvalid;
  moonshine_sdram_burst #(.POWERUP_CYCLES(20),.REFRESH_CYCLES(750)) controller(
   .clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(write_valid&&!force_stall),.request_ready(controller_ready),
   .request_write(1'b1),.request_address(write_address),.request_burst_data(write_data),
   .response_valid(rvalid),.response_data(rdata),.idle(mem_idle),.sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),
   .sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(ldqm),.sdram_udqm(udqm));
  sdram_model_burst model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(ldqm),.udqm(udqm),.dq(dq));'''),
 ('if(reset)begin busy<=0;req_count=0;held<=0;end', 'if(reset)begin req_count=0;held<=0;end'),
 ('   if(busy>0)busy<=busy-1;\n', ''),
 ('index=({8\'d0,write_address}-BASE)/8;memory[index]<=write_data;req_count=req_count+1;busy<=7;',
  'index=({8\'d0,write_address}-BASE)/8;req_count=req_count+1;'),
 ("if(bursts<MAX_BURSTS)memory[bursts]=128'hfeedfacedeadbeeffeedfacedeadbeef;",
  "if(bursts<MAX_BURSTS)model.mem[BASE+bursts*8]=16'hfeed;"),
 ('got=memory[i][j*8+:8];',
  'got=(j%2)?model.mem[BASE+i*8+j/2][15:8]:model.mem[BASE+i*8+j/2][7:0];'),
 ("if(bursts<MAX_BURSTS && memory[bursts]!==128'hfeedfacedeadbeeffeedfacedeadbeef)",
  "if(bursts<MAX_BURSTS && model.mem[BASE+bursts*8]!==16'hfeed)"),
 ('  $display("SDRAM_WRITER_PASS lengths=24 max_bytes=262144 tails=0..15 abort_drain=1 stalled_abort=1 stalled_fault=1 fault_drain=1");$finish;',
  '  if(model.refreshes<10 || model.write_bursts<16384 || model.writes!=model.write_bursts*8)$fatal(1,"model command accounting");\n  $display("SDRAM_WRITER_CONTROLLER_PASS lengths=24 max_bytes=262144 tails=0..15 abort_drain=1 stalled_abort=1 stalled_fault=1 fault_drain=1 refreshes=%0d write_bursts=%0d",model.refreshes,model.write_bursts);$finish;'),
]
for a,b in changes:
 if s.count(a)!=1:raise SystemExit('testbench anchor mismatch '+a[:120])
 s=s.replace(a,b)
Path(sys.argv[2]).write_text(s)
