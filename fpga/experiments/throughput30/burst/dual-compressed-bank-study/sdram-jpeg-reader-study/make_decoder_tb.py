#!/usr/bin/env python3
"""Make an SDRAM-fed frame-1 variant of the pinned staging contention bench."""
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
old=' word_reader reader(.clk(clk),.reset(reset),.start(start),.owned(read_ready&&!decode_done),.granted_length(decode_length),.start_accept(start_accept),.active(active),.error(error),.frame_done(frame_done),.byte_req(byte_req),.byte_addr(byte_addr),.byte_valid(read_valid),.byte_error(read_error),.byte_data(read_data),.out_valid(out_valid),.out_data(out_data),.out_strb(out_strb),.out_ready(dec_accept));'
new=''' wire br_start_accept,br_active,br_error,br_done,br_valid;wire[31:0]br_data;wire[3:0]br_strb;
 wire sd_start_accept,sd_active,sd_error,sd_done,sd_valid,sd_inflight,sd_fault;wire[31:0]sd_data;wire[3:0]sd_strb;
 wire sd_req;wire[23:0]sd_addr;
 word_reader reader(.clk(clk),.reset(reset),.start(start && current_id==0),.owned(read_ready&&!decode_done),.granted_length(decode_length),.start_accept(br_start_accept),.active(br_active),.error(br_error),.frame_done(br_done),.byte_req(byte_req),.byte_addr(byte_addr),.byte_valid(read_valid),.byte_error(read_error),.byte_data(read_data),.out_valid(br_valid),.out_data(br_data),.out_strb(br_strb),.out_ready(dec_accept));
 sdram_jpeg_reader sdreader(.clk(clk),.reset(reset),.start(start && current_id==1),.owned(read_ready&&!decode_done),.granted_length({16'd0,decode_length}),.start_accept(sd_start_accept),.active(sd_active),.error(sd_error),.frame_done(sd_done),.mem_req_valid(sd_req),.mem_req_ready(stage_rready),.mem_req_addr(sd_addr),.mem_data_valid(stage_dvalid),.mem_data(stage_rdata),.out_valid(sd_valid),.out_data(sd_data),.out_strb(sd_strb),.out_ready(dec_accept),.read_inflight(sd_inflight),.faulted(sd_fault));
 assign start_accept=current_id==0?br_start_accept:sd_start_accept;
 assign active=current_id==0?br_active:sd_active;
 assign error=(current_id==0?br_error:sd_error)||sd_fault;
 assign frame_done=current_id==0?br_done:sd_done;
 assign out_valid=current_id==0?br_valid:sd_valid;
 assign out_data=current_id==0?br_data:sd_data;
 assign out_strb=current_id==0?br_strb:sd_strb;'''
changes=[(old,new),
 ('wire stage_rvalid=stage_enable && stage_read_count<stage_total;', 'wire stage_rvalid=sd_req;'),
 ("wire[23:0] stage_raddr=24'h0e0000+24'(stage_read_count*8);", 'wire[23:0] stage_raddr=sd_addr;'),
 ('if(pixels!=345600||requests!=n||responses!=n||bytes_out!=n||words!=(n+3)/4)',
  'if(pixels!=345600||(id==0 && (requests!=n||responses!=n))||(id==1 && (requests!=0||responses!=0))||bytes_out!=n||words!=(n+3)/4)'),
 ('baseline_writes=model.writes;baseline_bursts=model.write_bursts;stage_enable=1;dump=$fopen(d1,"w");',
  '''baseline_writes=model.writes;baseline_bursts=model.write_bursts;stage_enable=1;
  while(stage_write_count<stage_total)@(negedge clk);
  stage_enable=0;while(!mem_idle)@(negedge clk);
  for(i=0;i<stage_total*8;i=i+1)if(model.mem[24'h060000+i]!==stage_word(i))$fatal(1,"predecode staging drain mismatch %0d",i);
  $display("STAGING_DRAIN_PASS bytes=%0d bursts=%0d",n1,stage_total);
  dump=$fopen(d1,"w");'''),
 ('STAGING_OVERLAP_PASS bytes=%0d bursts=%0d checked_words=%0d scan_grants=%0d decode_grants=%0d',
  'SDRAM_READER_INTEGRATION_PASS bytes=%0d bursts=%0d checked_words=%0d scan_grants=%0d decode_grants=%0d'),
]
for a,b in changes:
 if s.count(a)!=1:raise SystemExit('integration anchor mismatch: '+a[:120])
 s=s.replace(a,b)
Path(sys.argv[2]).write_text(s)
