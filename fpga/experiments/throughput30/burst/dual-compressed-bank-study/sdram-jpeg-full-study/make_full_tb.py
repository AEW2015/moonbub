#!/usr/bin/env python3
"""Connect the pinned experimental byte writer to the SDRAM-fed decoder bench."""
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
changes=[
 ('wire stage_wvalid=stage_enable && stage_write_count<stage_total;', 'wire stage_wvalid;'),
 ("wire[23:0] stage_waddr=24'h060000+24'(stage_write_count*8);", 'wire[23:0] stage_waddr;'),
 ("wire[127:0] stage_wdata=stage_block(stage_write_count*8) ^ ((stage_inject_corruption && stage_write_count==50)?128'd1:128'd0);",
  '''wire[127:0] writer_data;
 wire[127:0] stage_wdata=writer_data ^ ((stage_inject_corruption && stage_write_count==50)?128'd1:128'd0);
 reg writer_begin=0;integer writer_byte_count=0;
 wire writer_begin_ready,writer_begin_accept,writer_begin_reject,writer_byte_ready,writer_active,writer_done,writer_aborted,writer_failed,writer_faulted;
 wire[31:0]writer_accepted,writer_issued;
 sdram_jpeg_writer writer(.clk(clk),.reset(reset),.begin_valid(writer_begin),.begin_ready(writer_begin_ready),.declared_length(32'(n1)),
  .begin_accept(writer_begin_accept),.begin_reject(writer_begin_reject),.byte_valid(stage_enable && writer_byte_count<n1),.byte_ready(writer_byte_ready),.byte_data(jpg1[writer_byte_count]),
  .abort(1'b0),.sink_fault(1'b0),.write_drain_done(mem_idle),.write_valid(stage_wvalid),.write_ready(stage_wready),.write_address(stage_waddr),.write_data(writer_data),
  .active(writer_active),.done(writer_done),.aborted(writer_aborted),.failed(writer_failed),.faulted(writer_faulted),.accepted_bytes(writer_accepted),.issued_bursts(writer_issued));
 always @(posedge clk)if(!reset && stage_enable && writer_byte_count<n1 && writer_byte_ready)writer_byte_count<=writer_byte_count+1;'''),
 ('''  while(stage_write_count<stage_total)@(negedge clk);
  stage_enable=0;while(!mem_idle)@(negedge clk);''',
  '''  @(negedge clk);if(!writer_begin_ready)$fatal(1,"writer not ready");writer_begin=1;
  @(negedge clk);writer_begin=0;if(!writer_begin_accept||writer_begin_reject)$fatal(1,"writer begin rejected");
  while(!writer_done)begin @(negedge clk);if(writer_failed||writer_faulted||writer_aborted)$fatal(1,"writer failed");end
  if(writer_byte_count!=n1||writer_accepted!=n1||writer_issued!=stage_total||stage_write_count!=stage_total||!mem_idle)$fatal(1,"writer count/drain");
  stage_enable=0;'''),
 ('SDRAM_READER_INTEGRATION_PASS bytes=%0d bursts=%0d checked_words=%0d scan_grants=%0d decode_grants=%0d',
  'SDRAM_WRITER_READER_INTEGRATION_PASS bytes=%0d bursts=%0d checked_words=%0d scan_grants=%0d decode_grants=%0d'),
]
for old,new in changes:
 if s.count(old)!=1:raise SystemExit('writer integration anchor mismatch '+old[:120])
 s=s.replace(old,new)
Path(sys.argv[2]).write_text(s)
