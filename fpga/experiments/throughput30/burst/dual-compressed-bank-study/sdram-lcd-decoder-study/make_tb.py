#!/usr/bin/env python3
"""Derive a bounded staged-memory contention bench from pinned integration."""
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
changes=[
 ('moonshine_memory_burst memory(', 'moonshine_memory_staging memory('),
 ('.protocol_fault(protocol_fault),.sdram_a(a)',
  '.protocol_fault(protocol_fault),.jwrite_valid(stage_wvalid),.jwrite_ready(stage_wready),.jwrite_addr(stage_waddr),.jwrite_data(stage_wdata),.jread_valid(stage_rvalid),.jread_ready(stage_rready),.jread_addr(stage_raddr),.jread_data_valid(stage_dvalid),.jread_data(stage_rdata),.sdram_a(a)'),
 (' reg [7:0] jpg0[0:49151],jpg1[0:49151];reg seen[0:345599];reg [2047:0] f0,f1,d0,d1;integer fd,n0,n1,dump,pixels=0,requests=0,responses=0,words=0,bytes_out=0;reg finished=0;integer k,i;reg[31:0]crc0,crc1;',
 ''' reg [7:0] jpg0[0:49151],jpg1[0:49151];reg seen[0:345599];reg [2047:0] f0,f1,d0,d1;integer fd,n0,n1,dump,pixels=0,requests=0,responses=0,words=0,bytes_out=0;reg finished=0;integer k,i;reg[31:0]crc0,crc1;
 // The decoder continues reading the existing BRAM JPEG bank. These parallel
 // SDRAM clients exercise a second copy of fixture 1 solely as bus traffic.
 integer stage_total=0,stage_write_count=0,stage_read_count=0,stage_read_words=0,stage_scan_grants=0,stage_decode_grants=0;
 reg stage_enable=0,stage_inject_corruption=0;
 initial if($test$plusargs("STAGE_CORRUPT"))stage_inject_corruption=1;
 wire stage_wready,stage_rready,stage_dvalid;wire[15:0]stage_rdata;
 wire stage_wvalid=stage_enable && stage_write_count<stage_total;
 wire stage_rvalid=stage_enable && stage_read_count<stage_total;
 wire[23:0] stage_waddr=24'h060000+24'(stage_write_count*8);
 wire[23:0] stage_raddr=24'h0e0000+24'(stage_read_count*8);
 function automatic [15:0] stage_word(input integer idx);
  reg[7:0]lo,hi;begin lo=(idx*2<n1)?jpg1[idx*2]:0;hi=(idx*2+1<n1)?jpg1[idx*2+1]:0;stage_word={hi,lo};end
 endfunction
 function automatic [127:0] stage_block(input integer idx);
  integer j;begin for(j=0;j<8;j=j+1)stage_block[j*16+:16]=stage_word(idx+j);end
 endfunction
 wire[127:0] stage_wdata=stage_block(stage_write_count*8) ^ ((stage_inject_corruption && stage_write_count==50)?128'd1:128'd0);
 always @(posedge clk)if(!reset)begin
  if(stage_wready)stage_write_count<=stage_write_count+1;
  if(stage_rready)stage_read_count<=stage_read_count+1;
  if((stage_wready||stage_rready)&&scan_in_frame)stage_scan_grants<=stage_scan_grants+1;
  if((stage_wready||stage_rready)&&!dec_reset)stage_decode_grants<=stage_decode_grants+1;
  if(stage_dvalid)begin
   if(stage_read_words>=stage_total*8 || stage_rdata!==stage_word(stage_read_words))$fatal(1,"staging read mismatch word=%0d got=%h",stage_read_words,stage_rdata);
   stage_read_words<=stage_read_words+1;
  end
 end'''),
 ('while(!mem_idle||!tile_ready||tile_valid)@(negedge clk);',
  'while(!mem_idle||!tile_ready||tile_valid||(id==1 && (stage_write_count!=stage_total || stage_read_words!=stage_total*8)))@(negedge clk);'),
 ('if(model.writes-baseline_writes!=345600||model.write_bursts-baseline_bursts!=43200||underruns!=baseline_underruns)',
  'if(model.writes-baseline_writes!=345600+(id==1?stage_total*8:0)||model.write_bursts-baseline_bursts!=43200+(id==1?stage_total:0)||underruns!=baseline_underruns)'),
 ('for(i=0;i<384000;i=i+1)begin model.mem[i]=0;model.mem[24\'h080000+i]=0;end',
  '''for(i=0;i<384000;i=i+1)begin model.mem[i]=0;model.mem[24'h080000+i]=0;end
  stage_total=(n1+15)/16;
  for(i=0;i<stage_total*8;i=i+1)begin model.mem[24'h0e0000+i]=stage_word(i);model.mem[24'h060000+i]=16'hdead;end
  model.mem[24'h05ffff]=16'habcd;model.mem[24'h060000+stage_total*8]=16'hdcba;'''),
 ('baseline_writes=model.writes;baseline_bursts=model.write_bursts;dump=$fopen(d1,"w");',
  'baseline_writes=model.writes;baseline_bursts=model.write_bursts;stage_enable=1;dump=$fopen(d1,"w");'),
 ('if(accepted_frames!=2||dropped_frames!=0)$fatal(1,"frame accounting");$display("TEST_PASS_BANK_QSPI_SCANOUT");$finish;',
  '''if(accepted_frames!=2||dropped_frames!=0)$fatal(1,"frame accounting");
  if(underruns!=baseline_underruns)$fatal(1,"underruns through final scan");
  if(stage_write_count!=stage_total||stage_read_count!=stage_total||stage_read_words!=stage_total*8||stage_scan_grants==0||stage_decode_grants==0)$fatal(1,"staging accounting or overlap");
  for(i=0;i<stage_total*8;i=i+1)begin
   if(model.mem[24'h060000+i]!==stage_word(i)||model.mem[24'h0e0000+i]!==stage_word(i))$fatal(1,"staging memory mismatch %0d",i);
  end
  if(model.mem[24'h05ffff]!==16'habcd||model.mem[24'h060000+stage_total*8]!==16'hdcba)$fatal(1,"staging guard corrupted");
  $display("STAGING_OVERLAP_PASS bytes=%0d bursts=%0d checked_words=%0d scan_grants=%0d decode_grants=%0d",n1,stage_total,stage_read_words,stage_scan_grants,stage_decode_grants);
  $display("TEST_PASS_BANK_QSPI_SCANOUT");$finish;'''),
]
for a,b in changes:
 if s.count(a)!=1:raise SystemExit('testbench anchor mismatch: '+a[:100])
 s=s.replace(a,b)
Path(sys.argv[2]).write_text(s)
